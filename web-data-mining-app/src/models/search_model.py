class SearchModel:
    def __init__(self, data_mining_service):
        self.data_mining_service = data_mining_service

    def process_search_query(self, query):
        # Procesa la consulta y busca contactos
        return self.data_mining_service.search_contacts(query)