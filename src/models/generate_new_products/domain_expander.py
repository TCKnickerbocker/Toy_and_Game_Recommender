import random

class DomainExpander:
    def __init__(self):
        # Expanded core domain categories
        self.base_domains = [
            "board games", 
            "toys", 
            "video games", 
            "games for families",
            "party games",
            "cooperative games",
            "strategy games",
            "role-playing games",
            "STEM learning toys",
            "outdoor toys",
            "craft and DIY kits",
            "digital games and apps",
            "fitness and sports toys",
            "miniature and collectible games",
            "logic and puzzle games"
        ]
        
        # Expanded domain clusters with related sub-domains
        self.domain_clusters = {
            "entertainment": [
                "card games",
                "trivia games",
                "solo games", 
                "classic reimagined games",
                "digital hybrids"
            ],
            "educational": [
                "science kits", 
                "math games", 
                "language learning toys",
                "history simulation games",
                "coding toys",
                "geography games",
                "special needs learning toys",
                "cultural exploration toys",
                "financial literacy games"
            ],
            "physical_active": [
                "action figures", 
                "physical challenge games",
                "team building games",
                "adventure play sets",
                "water play toys"
            ],
            "creative": [
                "art kits", 
                "music-making toys", 
                "design challenge games",
                "storytelling games",
                "imagination toys"
            ],
            "technology_adjacent": [
                "electronic learning toys", 
                "augmented reality games", 
                "robotics kits", 
                "virtual interaction toys",
                "tech skill development games"
            ]
        }

    def get_random_domains(self, num_domains=4, include_base=True):
        """
        Retrieve a random subset of domains across clusters
        
        :param num_domains: Number of unique domains to return
        :param include_base: Whether to always include base domains
        :return: List of randomly selected domains
        """
        # Flatten all domain clusters
        all_domains = [
            domain 
            for cluster in self.domain_clusters.values() 
            for domain in cluster
        ]
        
        # Start with base domains if specified
        selected_domains = []
        if include_base:
            # Randomly select from base domains if num_domains is less than total base domains
            if num_domains < len(self.base_domains):
                selected_domains = random.sample(self.base_domains, num_domains)
            else:
                selected_domains = self.base_domains.copy()
        
        # Calculate how many additional domains we need
        remaining_slots = num_domains - len(selected_domains)
        
        # Only sample additional domains if we need more and have available domains
        if remaining_slots > 0:
            available_domains = [d for d in all_domains if d not in selected_domains]
            additional_domains = random.sample(
                available_domains,
                min(remaining_slots, len(available_domains))
            )
            selected_domains.extend(additional_domains)
        
        return selected_domains[:num_domains]
