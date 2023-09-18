output "confuent_cluster_url" {
  value = substr(confluent_kafka_cluster.demo.bootstrap_endpoint,11,-1)
}
output "confluent_api_key_id" {
  value = confluent_api_key.app-manager-kafka-api-key.id 
}

output "confluent_api_key_secret" {
  value = confluent_api_key.app-manager-kafka-api-key.secret
  sensitive = true
}
