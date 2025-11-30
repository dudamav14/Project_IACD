import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MetricsLogger:
    def __init__(self):
        self.logger = logging.getLogger("TechLinguaMetrics")

    def log_csp_efficiency(self, time_seconds, steps):
        self.logger.info(f"[METRIC - CSP] Tempo: {time_seconds:.4f}s | Passos Explorados: {steps}")

    def log_adversarial_decision(self, time_seconds, nodes_visited):
        self.logger.info(f"[METRIC - ADVERSARIAL] Tempo: {time_seconds:.4f}s | Nós Visitados: {nodes_visited}")