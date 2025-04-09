import os
import requests
import logging
import subprocess
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class NeptuneDataChecker:
    def __init__(self):
        """
        Initialize Neptune data checker with endpoint from environment.
        """
        try:
            # Get Neptune endpoint from environment
            self.neptune_endpoint = os.getenv('NEPTUNE_ENDPOINT')
            if not self.neptune_endpoint:
                raise ValueError("NEPTUNE_ENDPOINT not set in .env file")
            
            logger.info(f"Successfully initialized Neptune data checker with endpoint: {self.neptune_endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neptune data checker: {str(e)}")
            raise

    def execute_query(self, query: str) -> Dict:
        """
        Execute a Gremlin query against Neptune.
        
        Args:
            query: Gremlin query to execute
            
        Returns:
            Dict: Query results
        """
        try:
            # Prepare the request
            url = f"https://{self.neptune_endpoint}:8182/gremlin"
            headers = {'Content-Type': 'application/json'}
            payload = {"gremlin": query}
            
            # Execute the query
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute query: {str(e)}")
            raise

    def check_node_count(self) -> int:
        """
        Check the total number of nodes in Neptune.
        
        Returns:
            int: Total number of nodes
        """
        try:
            result = self.execute_query("g.V().count()")
            count = result['result']['data'][0]
            logger.info(f"Total nodes in Neptune: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to check node count: {str(e)}")
            raise

    def check_sample_nodes(self, limit: int = 5) -> List[Dict]:
        """
        Get a sample of nodes from Neptune.
        
        Args:
            limit: Number of nodes to return (default: 5)
            
        Returns:
            List[Dict]: List of sample nodes
        """
        try:
            query = f"g.V().limit({limit}).valueMap().with(WithOptions.tokens)"
            result = self.execute_query(query)
            nodes = result['result']['data']
            
            logger.info(f"Sample nodes ({len(nodes)}):")
            for node in nodes:
                logger.info(node)
                
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to get sample nodes: {str(e)}")
            raise

    def check_node_by_property(self, property_name: str, property_value: str) -> List[Dict]:
        """
        Find nodes by a specific property value.
        
        Args:
            property_name: Name of the property to search
            property_value: Value to search for
            
        Returns:
            List[Dict]: List of matching nodes
        """
        try:
            query = f"g.V().has('{property_name}', '{property_value}').valueMap().with(WithOptions.tokens)"
            result = self.execute_query(query)
            nodes = result['result']['data']
            
            logger.info(f"Found {len(nodes)} nodes with {property_name}='{property_value}'")
            for node in nodes:
                logger.info(node)
                
            return nodes
            
        except Exception as e:
            logger.error(f"Failed to find nodes by property: {str(e)}")
            raise

    def check_edge_count(self) -> int:
        """
        Check the total number of edges in Neptune.
        
        Returns:
            int: Total number of edges
        """
        try:
            result = self.execute_query("g.E().count()")
            count = result['result']['data'][0]
            logger.info(f"Total edges in Neptune: {count}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to check edge count: {str(e)}")
            raise

    def check_sample_edges(self, limit: int = 5) -> List[Dict]:
        """
        Get a sample of edges from Neptune.
        
        Args:
            limit: Number of edges to return (default: 5)
            
        Returns:
            List[Dict]: List of sample edges
        """
        try:
            query = f"g.E().limit({limit}).valueMap().with(WithOptions.tokens)"
            result = self.execute_query(query)
            edges = result['result']['data']
            
            logger.info(f"Sample edges ({len(edges)}):")
            for edge in edges:
                logger.info(edge)
                
            return edges
            
        except Exception as e:
            logger.error(f"Failed to get sample edges: {str(e)}")
            raise

    def execute_opencypher_query(self, query: str) -> Dict:
        """
        Execute an OpenCypher query against Neptune using curl.
        
        Args:
            query: OpenCypher query to execute
            
        Returns:
            Dict: Query results
        """
        try:
            # Prepare the curl command
            url = f"https://{self.neptune_endpoint}:8182/opencypher"
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Format the query for curl
            curl_command = [
                'curl',
                '-X', 'POST',
                url,
                '-H', f"Content-Type: {headers['Content-Type']}",
                '-H', f"Accept: {headers['Accept']}",
                '-d', f'{{"query": "{query}"}}'
            ]
            
            # Execute the curl command
            logger.info(f"Executing OpenCypher query: {query}")
            result = subprocess.run(curl_command, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Curl command failed: {result.stderr}")
                
            # Parse the response
            response = result.stdout
            return response
            
        except Exception as e:
            logger.error(f"Failed to execute OpenCypher query: {str(e)}")
            raise

    def check_opencypher_node_count(self) -> int:
        """
        Check the total number of nodes using OpenCypher.
        
        Returns:
            int: Total number of nodes
        """
        try:
            query = "MATCH (n) RETURN count(n) as count"
            result = self.execute_opencypher_query(query)
            logger.info(f"OpenCypher node count result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to check OpenCypher node count: {str(e)}")
            raise

    def check_opencypher_sample_nodes(self, limit: int = 5) -> Dict:
        """
        Get a sample of nodes using OpenCypher.
        
        Args:
            limit: Number of nodes to return (default: 5)
            
        Returns:
            Dict: Sample nodes
        """
        try:
            query = f"MATCH (n) RETURN n LIMIT {limit}"
            result = self.execute_opencypher_query(query)
            logger.info(f"OpenCypher sample nodes result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get OpenCypher sample nodes: {str(e)}")
            raise

    def check_opencypher_node_by_property(self, label: str, property_name: str, property_value: str) -> Dict:
        """
        Find nodes by a specific property value using OpenCypher.
        
        Args:
            label: Node label to search
            property_name: Name of the property to search
            property_value: Value to search for
            
        Returns:
            Dict: Matching nodes
        """
        try:
            query = f"MATCH (n:{label} {{{property_name}: '{property_value}'}}) RETURN n"
            result = self.execute_opencypher_query(query)
            logger.info(f"OpenCypher nodes by property result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to find OpenCypher nodes by property: {str(e)}")
            raise

    def check_opencypher_edge_count(self) -> int:
        """
        Check the total number of edges using OpenCypher.
        
        Returns:
            int: Total number of edges
        """
        try:
            query = "MATCH ()-[r]->() RETURN count(r) as count"
            result = self.execute_opencypher_query(query)
            logger.info(f"OpenCypher edge count result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to check OpenCypher edge count: {str(e)}")
            raise

    def check_opencypher_sample_edges(self, limit: int = 5) -> Dict:
        """
        Get a sample of edges using OpenCypher.
        
        Args:
            limit: Number of edges to return (default: 5)
            
        Returns:
            Dict: Sample edges
        """
        try:
            query = f"MATCH ()-[r]->() RETURN r LIMIT {limit}"
            result = self.execute_opencypher_query(query)
            logger.info(f"OpenCypher sample edges result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get OpenCypher sample edges: {str(e)}")
            raise

def main():
    """Main function to demonstrate Neptune data checking."""
    try:
        # Initialize checker
        checker = NeptuneDataChecker()
        
        # Check node count
        checker.check_node_count()
        
        # Check edge count
        checker.check_edge_count()
        
        # Get sample nodes
        checker.check_sample_nodes()
        
        # Get sample edges
        checker.check_sample_edges()
        
        # Example: Find nodes by NAME_FULL
        checker.check_node_by_property('NAME_FULL', 'John Doe')
        
        # Check node count using OpenCypher
        checker.check_opencypher_node_count()
        
        # Check edge count using OpenCypher
        checker.check_opencypher_edge_count()
        
        # Get sample nodes using OpenCypher
        checker.check_opencypher_sample_nodes()
        
        # Get sample edges using OpenCypher
        checker.check_opencypher_sample_edges()
        
        # Example: Find nodes by NAME_FULL using OpenCypher
        checker.check_opencypher_node_by_property('Person', 'NAME_FULL', 'John Doe')
        
    except Exception as e:
        logger.error(f"Error in Neptune data checking: {str(e)}")
        raise

if __name__ == "__main__":
    main() 