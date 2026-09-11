from typing import Tuple
try:
    from rapidfuzz import fuzz
except ImportError:
    import difflib
    class fuzz:
        @staticmethod
        def token_sort_ratio(s1, s2):
            return int(difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100)
        @staticmethod
        def token_set_ratio(s1, s2):
            return int(difflib.SequenceMatcher(None, s1.lower(), s2.lower()).ratio() * 100)

class CrossCheckEngine:
    @staticmethod
    def compare_names(name_a: str, name_b: str) -> Tuple[float, str]:
        """
        Fuzzy compares vendor entity names across documents.
        Returns: (match_score_0_to_100, status_MATCH_or_POTENTIAL_MISMATCH_or_MISMATCH)
        """
        if not name_a or not name_b:
            return 0.0, "MISSING_DATA"
            
        clean_a = name_a.upper().replace(".", "").replace(",", "").replace("PVT", "PRIVATE").replace("LTD", "LIMITED").strip()
        clean_b = name_b.upper().replace(".", "").replace(",", "").replace("PVT", "PRIVATE").replace("LTD", "LIMITED").strip()
        
        score = float(fuzz.token_sort_ratio(clean_a, clean_b))

        tokens_a = set(clean_a.split())
        tokens_b = set(clean_b.split())
        diff_tokens = tokens_a.symmetric_difference(tokens_b)

        if "UNIT" in diff_tokens or "BRANCH" in diff_tokens or "DIV" in diff_tokens or "PROPRIETORSHIP" in diff_tokens:
            score = min(score, 65.0)

        if score >= 90.0:
            status = "MATCH"
        elif score >= 60.0:
            status = "POTENTIAL_MISMATCH"
        else:
            status = "MISMATCH"
            
        return score, status

    @staticmethod
    def compare_addresses(addr_a: str, addr_b: str) -> Tuple[float, str]:
        """
        Fuzzy compares registered addresses across documents.
        Returns: (match_score_0_to_100, status)
        """
        if not addr_a or not addr_b:
            return 0.0, "MISSING_DATA"
            
        score = float(fuzz.token_sort_ratio(addr_a.lower(), addr_b.lower()))

        # Check key city/location tokens
        tokens_a = set(addr_a.upper().replace(",", " ").split())
        tokens_b = set(addr_b.upper().replace(",", " ").split())

        # Major Indian industrial cities
        cities = {"PUNE", "NAGPUR", "MUMBAI", "DELHI", "JAIPUR", "CHENNAI", "BANGALORE", "KOLKATA", "HYDERABAD", "AHMEDABAD"}
        cities_in_a = tokens_a.intersection(cities)
        cities_in_b = tokens_b.intersection(cities)

        if cities_in_a and cities_in_b and cities_in_a != cities_in_b:
            score = min(score, 45.0)

        if score >= 80.0:
            status = "MATCH"
        elif score >= 50.0:
            status = "POTENTIAL_MISMATCH"
        else:
            status = "MISMATCH"
            
        return score, status
