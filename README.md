# streamlit ui from json config file (app.py)
1) Setup config file as per example [app](json-driven-app-metadata.json)
2) Run ```source app.sh``` to deploy streamlit app

# streamlit ui from Neo4j metadata (app_graph.py)

1) Set environment variables NEO4J_HOST, NEO4J_USER, NEO4J_PASSWORD for connection to Neo4j database
2) Use https://arrows.app/ to create app metadata (see example [app](data/graph-driven-app-metadata.json))
3) Update ```app.sh``` by replacing app.py with app_graph.py and run ```source app.sh``` to deploy streamlit app 