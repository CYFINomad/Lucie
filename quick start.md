Launch appl : `docker-compose -f docker-compose.dev.yml up -d`
View log : `docker logs containter-name`
Rebuild container: `docker-compose build`

Delete all container : `docker rm -f $(docker ps -aq)`
Delete all image : `docker system prune -a --volumes`
