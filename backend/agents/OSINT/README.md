# OSINT Agents

This directory contains various OSINT (Open Source Intelligence) agents that help with investigations by gathering and analyzing publicly available information.

## Structure

- `core/` - Core OSINT functionality and utilities
- `agents/` - Individual OSINT agent implementations
  - `domain/` - Domain-related investigations
  - `social/` - Social media investigations
  - `company/` - Company and business investigations
  - `person/` - Person of interest investigations
- `output/` - Output formats and generators
  - `maltego/` - Maltego transform and entity definitions
  - `markdown/` - Markdown report templates
  - `json/` - JSON data structures
- `api/` - API integrations and clients
- `utils/` - Utility functions and helpers

## Features

- Automated data collection from various sources
- Maltego integration for visual investigation maps
- Markdown report generation
- Data correlation and analysis
- API integrations with popular OSINT tools and services
- Export capabilities in multiple formats

## Usage

Each agent can be used independently or as part of a larger investigation workflow. The agents support:

1. Data collection from multiple sources
2. Data correlation and analysis
3. Report generation in various formats
4. Maltego integration for visual mapping
5. Export capabilities for further analysis

## Configuration

API keys and configuration settings should be stored in the appropriate configuration files and never committed to the repository. 