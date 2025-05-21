from typing import Dict, List, Any, Optional, Union, Tuple, Set
import logging
import re
import json
import hashlib
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import httpx

from ..knowledge.knowledge_graph import KnowledgeGraph
from ..knowledge.vector_store import VectorStore
from ..knowledge.cross_domain_knowledge_graph import CrossDomainKnowledgeGraph


class URLKnowledgeExtractor:
    """
    Service d'extraction de connaissances à partir d'URLs.
    Analyse le contenu web pour extraire des concepts et les intégrer dans la base de connaissances.
    """

    def __init__(
        self,
        knowledge_graph: KnowledgeGraph,
        vector_store: VectorStore,
        cross_domain_kg: Optional[CrossDomainKnowledgeGraph] = None,
    ):
        """
        Initialise l'extracteur de connaissances à partir d'URLs.

        Args:
            knowledge_graph (KnowledgeGraph): Instance du graphe de connaissances
            vector_store (VectorStore): Instance du stockage vectoriel
            cross_domain_kg (Optional[CrossDomainKnowledgeGraph], optional): Instance du gestionnaire de graphe multi-domaines
        """
        self.logger = logging.getLogger(__name__)
        self.kg = knowledge_graph
        self.vs = vector_store
        self.cross_domain_kg = cross_domain_kg
        self.http_client = httpx.Client(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "Lucie Knowledge Extractor/1.0"},
        )

        # Paramètres de configuration
        self.min_paragraph_length = (
            100  # Longueur minimale d'un paragraphe à considérer
        )
        self.max_concepts_per_url = 15  # Nombre maximum de concepts à extraire par URL

        # Stocker les URLs déjà extraites
        self.processed_urls = set()

    def extract_from_url(
        self, url: str, domain: str = "general", max_depth: int = 0
    ) -> Dict[str, Any]:
        """
        Extrait des connaissances depuis une URL et les ajoute au graphe.

        Args:
            url (str): URL à extraire
            domain (str, optional): Domaine de connaissances. Par défaut à "general".
            max_depth (int, optional): Profondeur maximale de crawling. Par défaut à 0.

        Returns:
            Dict[str, Any]: Résultats de l'extraction
        """
        # Vérifier si l'URL a déjà été traitée
        if url in self.processed_urls:
            self.logger.info(f"URL déjà traitée: {url}")
            return {"url": url, "status": "already_processed", "concepts_added": 0}

        # Normaliser l'URL
        url = self._normalize_url(url)

        try:
            # Extraire le contenu de l'URL
            html_content, status_code = self._fetch_url(url)

            if not html_content or status_code >= 400:
                self.logger.error(
                    f"Échec de l'extraction de l'URL {url}: statut {status_code}"
                )
                return {"url": url, "status": "error", "status_code": status_code}

            # Analyser le contenu HTML
            title, text_content, meta_description, links = self._parse_html(
                html_content, url
            )

            # Enregistrer l'URL dans le graphe
            url_id = self._create_url_node(url, title, meta_description, domain)

            # Segmenter le contenu en paragraphes
            paragraphs = self._segment_content(text_content)

            # Extraire les concepts
            concepts = self._extract_concepts_from_paragraphs(paragraphs, url)

            # Ajouter les concepts au graphe et au stockage vectoriel
            added_concepts = self._add_concepts_to_knowledge_base(
                concepts, domain, url_id
            )

            # Ajouter à la liste des URLs traitées
            self.processed_urls.add(url)

            # Traiter récursivement les liens si max_depth > 0
            child_results = []
            if max_depth > 0 and links:
                for link in links[:5]:  # Limiter à 5 liens pour éviter une explosion
                    if link not in self.processed_urls:
                        child_result = self.extract_from_url(
                            link, domain, max_depth - 1
                        )
                        child_results.append(child_result)

            # Construire le résultat
            result = {
                "url": url,
                "status": "success",
                "title": title,
                "concepts_extracted": len(concepts),
                "concepts_added": len(added_concepts),
                "child_urls_processed": len(child_results),
                "child_results": child_results if max_depth > 0 else None,
            }

            return result

        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction depuis {url}: {e}")
            return {"url": url, "status": "error", "error": str(e)}

    def extract_from_urls(
        self, urls: List[str], domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Extrait des connaissances à partir d'une liste d'URLs.

        Args:
            urls (List[str]): Liste d'URLs à traiter
            domain (str, optional): Domaine de connaissances. Par défaut à "general".

        Returns:
            Dict[str, Any]: Résultats globaux de l'extraction
        """
        results = []
        total_concepts_added = 0
        success_count = 0
        error_count = 0

        for url in urls:
            result = self.extract_from_url(url, domain)
            results.append(result)

            if result["status"] == "success":
                success_count += 1
                total_concepts_added += result.get("concepts_added", 0)
            elif result["status"] == "error":
                error_count += 1

        return {
            "total_urls": len(urls),
            "success_count": success_count,
            "error_count": error_count,
            "already_processed_count": len(urls) - success_count - error_count,
            "total_concepts_added": total_concepts_added,
            "detailed_results": results,
        }

    def extract_from_content(
        self, content: str, source_url: str, domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Extrait des connaissances à partir d'un contenu HTML/texte fourni directement.

        Args:
            content (str): Contenu à analyser (HTML ou texte)
            source_url (str): URL source du contenu (pour référence)
            domain (str, optional): Domaine de connaissances. Par défaut à "general".

        Returns:
            Dict[str, Any]: Résultats de l'extraction
        """
        try:
            # Déterminer si le contenu est du HTML ou du texte brut
            is_html = bool(re.search(r"<\s*html", content, re.IGNORECASE))

            if is_html:
                # Analyser le contenu HTML
                title, text_content, meta_description, _ = self._parse_html(
                    content, source_url
                )
            else:
                # Contenu texte
                text_content = content
                title = "Contenu importé"
                meta_description = "Contenu texte importé sans métadonnées"

            # Enregistrer l'URL source dans le graphe
            url_id = self._create_url_node(source_url, title, meta_description, domain)

            # Segmenter le contenu en paragraphes
            paragraphs = self._segment_content(text_content)

            # Extraire les concepts
            concepts = self._extract_concepts_from_paragraphs(paragraphs, source_url)

            # Ajouter les concepts au graphe et au stockage vectoriel
            added_concepts = self._add_concepts_to_knowledge_base(
                concepts, domain, url_id
            )

            # Construire le résultat
            result = {
                "source_url": source_url,
                "status": "success",
                "title": title,
                "concepts_extracted": len(concepts),
                "concepts_added": len(added_concepts),
            }

            return result

        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction du contenu fourni: {e}")
            return {"source_url": source_url, "status": "error", "error": str(e)}

    def extract_from_sitemap(
        self, sitemap_url: str, domain: str = "general", max_urls: int = 20
    ) -> Dict[str, Any]:
        """
        Extrait des connaissances à partir d'un sitemap XML.

        Args:
            sitemap_url (str): URL du sitemap XML
            domain (str, optional): Domaine de connaissances. Par défaut à "general".
            max_urls (int, optional): Nombre maximum d'URLs à traiter. Par défaut à 20.

        Returns:
            Dict[str, Any]: Résultats de l'extraction
        """
        try:
            # Récupérer le contenu du sitemap
            sitemap_content, status_code = self._fetch_url(sitemap_url)

            if not sitemap_content or status_code >= 400:
                self.logger.error(
                    f"Échec de la récupération du sitemap {sitemap_url}: statut {status_code}"
                )
                return {
                    "sitemap_url": sitemap_url,
                    "status": "error",
                    "status_code": status_code,
                }

            # Parser le XML
            soup = BeautifulSoup(sitemap_content, "lxml-xml")

            # Extraire les URLs
            url_elements = soup.find_all("loc")
            urls = [element.text for element in url_elements][:max_urls]

            # Traiter chaque URL
            self.logger.info(
                f"Extraction de {len(urls)} URLs depuis le sitemap {sitemap_url}"
            )
            results = self.extract_from_urls(urls, domain)

            # Ajouter l'URL du sitemap aux résultats
            results["sitemap_url"] = sitemap_url

            return results

        except Exception as e:
            self.logger.error(
                f"Erreur lors de l'extraction depuis le sitemap {sitemap_url}: {e}"
            )
            return {"sitemap_url": sitemap_url, "status": "error", "error": str(e)}

    def _normalize_url(self, url: str) -> str:
        """
        Normalise une URL pour éviter les duplications.

        Args:
            url (str): URL à normaliser

        Returns:
            str: URL normalisée
        """
        # Ajouter le schéma http:// si manquant
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        # Parser l'URL
        parsed_url = urlparse(url)

        # Supprimer les fragments
        normalized = parsed_url._replace(fragment="").geturl()

        # Supprimer les paramètres de suivi courants comme utm_*
        if "?" in normalized:
            base, params = normalized.split("?", 1)
            param_pairs = params.split("&")
            filtered_params = [
                p for p in param_pairs if not p.startswith(("utm_", "ref=", "source="))
            ]

            if filtered_params:
                normalized = base + "?" + "&".join(filtered_params)
            else:
                normalized = base

        return normalized

    def _fetch_url(self, url: str) -> Tuple[Optional[str], int]:
        """
        Récupère le contenu d'une URL.

        Args:
            url (str): URL à récupérer

        Returns:
            Tuple[Optional[str], int]: Tuple contenant le contenu et le code de statut HTTP
        """
        try:
            response = self.http_client.get(url)
            response.raise_for_status()

            # Détecter l'encodage du contenu
            content_type = response.headers.get("content-type", "")
            charset = re.search(r"charset=(\S+)", content_type)

            if charset:
                encoding = charset.group(1)
            else:
                # Utiliser l'encodage apparent
                encoding = response.apparent_encoding or "utf-8"

            # Décoder le contenu
            content = response.text

            return content, response.status_code

        except httpx.HTTPStatusError as e:
            self.logger.error(
                f"Erreur HTTP lors de la récupération de {url}: {e.response.status_code}"
            )
            return None, e.response.status_code
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de {url}: {e}")
            return None, 500

    def _parse_html(
        self, html_content: str, url: str
    ) -> Tuple[str, str, str, List[str]]:
        """
        Parse le contenu HTML pour en extraire les éléments pertinents.

        Args:
            html_content (str): Contenu HTML à analyser
            url (str): URL source du contenu

        Returns:
            Tuple[str, str, str, List[str]]: Tuple (titre, contenu texte, méta-description, liens)
        """
        soup = BeautifulSoup(html_content, "lxml")

        # Extraire le titre
        title_element = soup.find("title")
        title = title_element.text.strip() if title_element else "Sans titre"

        # Extraire la méta-description
        meta_desc_element = soup.find("meta", attrs={"name": "description"})
        meta_description = (
            meta_desc_element.get("content", "") if meta_desc_element else ""
        )

        # Supprimer les scripts, styles et autres éléments non pertinents
        for element in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            element.decompose()

        # Extraire le texte principal
        text_content = ""

        # Essayer d'abord de trouver le contenu principal
        main_content = soup.find(
            ["article", "main", "div", "section"],
            class_=lambda c: c
            and any(
                x in str(c).lower() for x in ["content", "article", "main", "post"]
            ),
        )

        if main_content:
            # Extraire le texte du contenu principal
            paragraphs = main_content.find_all(
                ["p", "h1", "h2", "h3", "h4", "h5", "h6", "li"]
            )
            text_content = "\n\n".join([p.get_text().strip() for p in paragraphs])
        else:
            # Sinon, extraire tous les paragraphes
            paragraphs = soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6"])
            text_content = "\n\n".join([p.get_text().strip() for p in paragraphs])

        # Extraire les liens
        base_url = self._get_base_url(url)
        links = []

        for link in soup.find_all("a", href=True):
            href = link["href"]

            # Ignorer les ancres et les liens javascript
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            # Construire l'URL complète
            if not href.startswith(("http://", "https://")):
                if href.startswith("/"):
                    href = base_url + href
                else:
                    href = base_url + "/" + href

            # Normaliser et ajouter à la liste
            normalized_href = self._normalize_url(href)

            # Vérifier que l'URL est du même domaine
            href_domain = urlparse(normalized_href).netloc
            url_domain = urlparse(url).netloc

            if href_domain == url_domain and normalized_href not in links:
                links.append(normalized_href)

        return title, text_content, meta_description, links

    def _get_base_url(self, url: str) -> str:
        """
        Extrait l'URL de base (schéma + domaine) d'une URL complète.

        Args:
            url (str): URL complète

        Returns:
            str: URL de base
        """
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _segment_content(self, text_content: str) -> List[str]:
        """
        Segmente le contenu textuel en paragraphes.

        Args:
            text_content (str): Contenu textuel

        Returns:
            List[str]: Liste des paragraphes
        """
        # Segmenter par lignes vides
        segments = re.split(r"\n\s*\n", text_content)

        # Nettoyer les segments
        cleaned_segments = []

        for segment in segments:
            # Supprimer les espaces en trop
            segment = re.sub(r"\s+", " ", segment).strip()

            # Ne garder que les segments assez longs
            if len(segment) >= self.min_paragraph_length:
                cleaned_segments.append(segment)

        return cleaned_segments

    def _extract_concepts_from_paragraphs(
        self, paragraphs: List[str], source_url: str
    ) -> List[Dict[str, Any]]:
        """
        Extrait des concepts à partir des paragraphes.

        Args:
            paragraphs (List[str]): Liste des paragraphes
            source_url (str): URL source

        Returns:
            List[Dict[str, Any]]: Liste des concepts extraits
        """
        concepts = []

        for i, paragraph in enumerate(paragraphs):
            # Générer un ID de concept basé sur l'URL et le contenu
            content_hash = hashlib.md5(paragraph.encode("utf-8")).hexdigest()[:10]
            concept_id = f"url_concept:{content_hash}"

            # Extraire un titre pour le concept (première phrase ou début du paragraphe)
            first_sentence_match = re.match(r"^(.*?[.!?])\s", paragraph)
            if first_sentence_match:
                name = first_sentence_match.group(1)
                # Limiter la longueur du nom
                if len(name) > 100:
                    name = name[:97] + "..."
            else:
                # Utiliser le début du paragraphe
                name = paragraph[:50] + ("..." if len(paragraph) > 50 else "")

            # Créer le concept
            concept = {
                "id": concept_id,
                "name": name,
                "description": paragraph,
                "source_url": source_url,
                "confidence": 0.8,  # Valeur par défaut
                "paragraph_index": i,
            }

            concepts.append(concept)

            # Limiter le nombre total de concepts
            if len(concepts) >= self.max_concepts_per_url:
                break

        return concepts

    def _create_url_node(
        self, url: str, title: str, meta_description: str, domain: str
    ) -> str:
        """
        Crée un noeud représentant l'URL dans le graphe de connaissances.

        Args:
            url (str): URL
            title (str): Titre de la page
            meta_description (str): Méta-description
            domain (str): Domaine de connaissances

        Returns:
            str: ID du noeud créé
        """
        # Générer un ID unique pour l'URL
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()[:10]
        url_id = f"url:{url_hash}"

        # Propriétés du noeud
        url_properties = {
            "type": "url",
            "url": url,
            "title": title,
            "description": meta_description,
            "domain": domain,
            "timestamp": self._get_timestamp(),
        }

        # Ajouter au graphe
        self.kg.add_concept(url_id, url_properties)

        # Si le cross_domain_kg est disponible, l'ajouter au domaine approprié
        if self.cross_domain_kg:
            self.cross_domain_kg.add_concept_to_domain(url_id, domain, url_properties)

        return url_id

    def _add_concepts_to_knowledge_base(
        self, concepts: List[Dict[str, Any]], domain: str, url_id: str
    ) -> List[str]:
        """
        Ajoute les concepts extraits à la base de connaissances.

        Args:
            concepts (List[Dict[str, Any]]): Liste des concepts à ajouter
            domain (str): Domaine de connaissances
            url_id (str): ID du noeud URL source

        Returns:
            List[str]: IDs des concepts ajoutés
        """
        added_concepts = []

        for concept in concepts:
            concept_id = concept["id"]

            # Vérifier si le concept existe déjà
            existing_concept = self.kg.get_concept(concept_id)

            if not existing_concept:
                # Préparer les propriétés du concept
                concept_properties = {
                    "name": concept["name"],
                    "description": concept["description"],
                    "source_type": "url",
                    "source": concept["source_url"],
                    "confidence": concept.get("confidence", 0.8),
                    "extracted_at": self._get_timestamp(),
                }

                # Ajouter au graphe de connaissances
                concept_added = self.kg.add_concept(concept_id, concept_properties)

                if concept_added:
                    # Ajouter également au stockage vectoriel
                    try:
                        self.vs.add_concept(
                            concept_id=concept_id,
                            name=concept["name"],
                            description=concept["description"],
                            category=domain,
                            source="web",
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Erreur lors de l'ajout au stockage vectoriel: {e}"
                        )

                    # Créer une relation avec l'URL source
                    self.kg.add_relationship(
                        concept_id,
                        url_id,
                        "EXTRACTED_FROM",
                        {"confidence": concept.get("confidence", 0.8)},
                    )

                    # Si le cross_domain_kg est disponible, l'ajouter au domaine approprié
                    if self.cross_domain_kg:
                        self.cross_domain_kg.add_concept_to_domain(
                            concept_id, domain, concept_properties
                        )

                    added_concepts.append(concept_id)
            else:
                # Mettre à jour la relation avec l'URL source
                self.kg.add_relationship(
                    concept_id,
                    url_id,
                    "ALSO_FOUND_IN",
                    {"confidence": concept.get("confidence", 0.8)},
                )

        return added_concepts

    def _get_timestamp(self) -> str:
        """Retourne le timestamp actuel."""
        from datetime import datetime

        return datetime.now().isoformat()
