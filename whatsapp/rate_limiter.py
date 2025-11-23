"""
Rate Limiter pour protection anti-ban WhatsApp
"""
import time
from datetime import datetime, timedelta
from collections import deque
from typing import Optional, Dict
import random

class RateLimiter:
    """
    Gère les limites d'envoi pour éviter les bans WhatsApp
    """
    
    def __init__(self, 
                 messages_per_minute: int = 10,
                 messages_per_hour: int = 200,
                 messages_per_day: int = 1000,
                 random_delay: bool = True):
        self.messages_per_minute = messages_per_minute
        self.messages_per_hour = messages_per_hour
        self.messages_per_day = messages_per_day
        self.random_delay = random_delay
        
        # Historique des envois
        self.envois_minute = deque()  # Timestamps des dernières minutes
        self.envois_heure = deque()   # Timestamps de la dernière heure
        self.envois_jour = deque()    # Timestamps du jour
        
        # État
        self.paused = False
        self.stopped = False
    
    def can_send(self) -> tuple[bool, Optional[str]]:
        """
        Vérifie si on peut envoyer un message
        Retourne (can_send, reason_if_not)
        """
        if self.stopped:
            return False, "Campagne arrêtée"
        
        if self.paused:
            return False, "Campagne en pause"
        
        now = datetime.now()
        
        # Nettoyer les anciens envois
        self._clean_old_envois(now)
        
        # Vérifier limite minute
        if len(self.envois_minute) >= self.messages_per_minute:
            next_available = self.envois_minute[0] + timedelta(minutes=1)
            wait_seconds = (next_available - now).total_seconds()
            return False, f"Limite minute atteinte. Attente: {int(wait_seconds)}s"
        
        # Vérifier limite heure
        if len(self.envois_heure) >= self.messages_per_hour:
            next_available = self.envois_heure[0] + timedelta(hours=1)
            wait_seconds = (next_available - now).total_seconds()
            return False, f"Limite heure atteinte. Attente: {int(wait_seconds/60)}min"
        
        # Vérifier limite jour
        if len(self.envois_jour) >= self.messages_per_day:
            return False, "Limite jour atteinte. Reprendre demain"
        
        return True, None
    
    def record_send(self):
        """Enregistre un envoi"""
        now = datetime.now()
        self.envois_minute.append(now)
        self.envois_heure.append(now)
        self.envois_jour.append(now)
    
    def _clean_old_envois(self, now: datetime):
        """Nettoie les envois trop anciens"""
        # Nettoyer minute (garder dernière minute)
        while self.envois_minute and (now - self.envois_minute[0]).total_seconds() > 60:
            self.envois_minute.popleft()
        
        # Nettoyer heure (garder dernière heure)
        while self.envois_heure and (now - self.envois_heure[0]).total_seconds() > 3600:
            self.envois_heure.popleft()
        
        # Nettoyer jour (garder aujourd'hui)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        while self.envois_jour and self.envois_jour[0] < today_start:
            self.envois_jour.popleft()
    
    def get_wait_time(self) -> float:
        """
        Calcule le temps d'attente avant prochain envoi
        """
        can_send, reason = self.can_send()
        
        if can_send:
            # Délai aléatoire si activé (3-10 secondes)
            if self.random_delay:
                return random.uniform(3, 10)
            else:
                # Délai minimum entre messages
                if len(self.envois_minute) > 0:
                    return max(0, 60 / self.messages_per_minute)
                return 1
        
        # Si limite atteinte, calculer temps d'attente
        now = datetime.now()
        
        if len(self.envois_minute) >= self.messages_per_minute:
            next_available = self.envois_minute[0] + timedelta(minutes=1)
            return max(0, (next_available - now).total_seconds())
        
        if len(self.envois_heure) >= self.messages_per_hour:
            next_available = self.envois_heure[0] + timedelta(hours=1)
            return max(0, (next_available - now).total_seconds())
        
        return 0
    
    def get_stats(self) -> Dict:
        """Retourne les statistiques actuelles"""
        now = datetime.now()
        self._clean_old_envois(now)
        
        return {
            'minute': {
                'envoyes': len(self.envois_minute),
                'limite': self.messages_per_minute,
                'restants': max(0, self.messages_per_minute - len(self.envois_minute))
            },
            'heure': {
                'envoyes': len(self.envois_heure),
                'limite': self.messages_per_hour,
                'restants': max(0, self.messages_per_hour - len(self.envois_heure))
            },
            'jour': {
                'envoyes': len(self.envois_jour),
                'limite': self.messages_per_day,
                'restants': max(0, self.messages_per_day - len(self.envois_jour))
            },
            'paused': self.paused,
            'stopped': self.stopped
        }
    
    def pause(self):
        """Met en pause"""
        self.paused = True
    
    def resume(self):
        """Reprend"""
        self.paused = False
    
    def stop(self):
        """Arrête complètement"""
        self.stopped = True
    
    def reset(self):
        """Réinitialise (pour nouvelle campagne)"""
        self.stopped = False
        self.paused = False
        self.envois_minute.clear()
        self.envois_heure.clear()
        self.envois_jour.clear()

