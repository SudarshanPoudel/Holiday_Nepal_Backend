FROM neo4j:5.10

# Install GDS plugin
RUN wget https://graphdatascience.ninja/neo4j-graph-data-science-2.5.7.jar \
    -O /var/lib/neo4j/plugins/graph-data-science.jar

# Install APOC Extended for Neo4j 5.10.x
RUN wget https://github.com/neo4j-contrib/neo4j-apoc-procedures/releases/download/5.10.0/apoc-5.10.0-extended.jar \
    -O /var/lib/neo4j/plugins/apoc.jar
