# Kaleidos legacy conversion

Get the required containers running:
```
docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml up
```

Create dump of all mu-file objects: 
```
docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_file_dump.py
```

Create a dump for VR: 
```

docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_vr_dump.py
```

Create a dump for OC: 
```
docker-compose -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_oc_dump.py
```
