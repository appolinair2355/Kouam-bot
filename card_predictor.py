"""
Card prediction logic for Joker's Telegram Bot - simplified for webhook deployment
"""

import re
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
import time
import os
import json

logger = logging.getLogger(__name__)

# Configuration constants
VALID_CARD_COMBINATIONS = [
    "♠️♥️♦️", "♠️♥️♣️", "♠️♦️♣️", "♥️♦️♣️"
]

CARD_SYMBOLS = ["♠️", "♥️", "♦️", "♣️", "❤️"]  # Include both ♥️ and ❤️ variants

# PREDICTION_MESSAGE is now handled directly in make_prediction method

# Target channel ID for Baccarat Kouamé
TARGET_CHANNEL_ID = -1002682552255

# Target channel ID for predictions and updates
PREDICTION_CHANNEL_ID = -1002646551216

class CardPredictor:
    """Handles card prediction logic for webhook deployment"""

    def __init__(self):
        self.predictions = {}  # Store predictions for verification
        self.processed_messages = set()  # Avoid duplicate processing
        self.sent_predictions = {}  # Store sent prediction messages for editing
        self.temporary_messages = {}  # Store temporary messages waiting for final edit
        self.pending_edits = {}  # Store messages waiting for edit with indicators
        self.position_preference = 1  # Default position preference (1 = first card, 2 = second card)
        self.redirect_channels = {}  # Store redirection channels for different chats
        self.last_prediction_time = self._load_last_prediction_time()  # Load persisted timestamp
        self.prediction_cooldown = 190  # Cooldown period in seconds between predictions

    def _load_last_prediction_time(self) -> float:
        """Load last prediction timestamp from file"""
        try:
            if os.path.exists('.last_prediction_time'):
                with open('.last_prediction_time', 'r') as f:
                    timestamp = float(f.read().strip())
                    logger.info(f"⏰ PERSISTANCE - Dernière prédiction chargée: {time.time() - timestamp:.1f}s écoulées")
                    return timestamp
        except Exception as e:
            logger.warning(f"⚠️ Impossible de charger le timestamp: {e}")
        return 0
    
    def _save_last_prediction_time(self):
        """Save last prediction timestamp to file"""
        try:
            with open('.last_prediction_time', 'w') as f:
                f.write(str(self.last_prediction_time))
        except Exception as e:
            logger.warning(f"⚠️ Impossible de sauvegarder le timestamp: {e}")

    def reset_predictions(self):
        """Reset all prediction states - useful for recalibration"""
        self.predictions.clear()
        self.processed_messages.clear()
        self.sent_predictions.clear()
        self.temporary_messages.clear()
        self.pending_edits.clear()
        self.last_prediction_time = 0
        self._save_last_prediction_time()
        logger.info("🔄 Système de prédictions réinitialisé")

    def set_position_preference(self, position: int):
        """Set the position preference for card selection (1 or 2)"""
        if position in [1, 2]:
            self.position_preference = position
            logger.info(f"🎯 Position de carte mise à jour : {position}")
        else:
            logger.warning(f"⚠️ Position invalide : {position}. Utilisation de la position par défaut (1).")
    
    def set_redirect_channel(self, source_chat_id: int, target_chat_id: int):
        """Set redirection channel for predictions from a source chat"""
        self.redirect_channels[source_chat_id] = target_chat_id
        logger.info(f"📤 Redirection configurée : {source_chat_id} → {target_chat_id}")
    
    def get_redirect_channel(self, source_chat_id: int) -> int:
        """Get redirect channel for a source chat, fallback to PREDICTION_CHANNEL_ID"""
        return self.redirect_channels.get(source_chat_id, PREDICTION_CHANNEL_ID)
    
    def reset_all_predictions(self):
        """Reset all predictions and redirect channels"""
        self.predictions.clear()
        self.processed_messages.clear()
        self.sent_predictions.clear()
        self.temporary_messages.clear()
        self.pending_edits.clear()
        self.redirect_channels.clear()
        self.last_prediction_time = 0
        self._save_last_prediction_time()
        logger.info("🔄 Toutes les prédictions et redirections ont été supprimées")

    def extract_game_number(self, message: str) -> Optional[int]:
        """Extract game number from message like #n744 or #N744"""
        pattern = r'#[nN](\d+)'
        match = re.search(pattern, message)
        if match:
            return int(match.group(1))
        return None

    def extract_cards_from_parentheses(self, message: str) -> List[str]:
        """Extract cards from first and second parentheses"""
        # This method is deprecated, use extract_card_symbols_from_parentheses instead
        return []

    def has_pending_indicators(self, text: str) -> bool:
        """Check if message contains indicators suggesting it will be edited"""
        indicators = ['⏰', '▶', '🕐', '➡️']
        return any(indicator in text for indicator in indicators)

    def has_completion_indicators(self, text: str) -> bool:
        """Check if message contains completion indicators after edit"""
        completion_indicators = ['✅', '🔰']
        has_indicator = any(indicator in text for indicator in completion_indicators)
        if has_indicator:
            logger.info(f"🔍 FINALISATION DÉTECTÉE - Indicateurs trouvés dans: {text[:100]}...")
        return has_indicator

    def should_wait_for_edit(self, text: str, message_id: int) -> bool:
        """Determine if we should wait for this message to be edited"""
        if self.has_pending_indicators(text):
            # Store this message as pending edit
            self.pending_edits[message_id] = {
                'original_text': text,
                'timestamp': datetime.now()
            }
            return True
        return False

    def extract_card_symbols_from_parentheses(self, text: str) -> List[List[str]]:
        """Extract unique card symbols from each parentheses section"""
        # Find all parentheses content
        pattern = r'\(([^)]+)\)'
        matches = re.findall(pattern, text)

        all_sections = []
        for match in matches:
            # Normalize ❤️ to ♥️ for consistency
            normalized_content = match.replace("❤️", "♥️")

            # Extract only unique card symbols (costumes) from this section
            unique_symbols = set()
            for symbol in ["♠️", "♥️", "♦️", "♣️"]:
                if symbol in normalized_content:
                    unique_symbols.add(symbol)

            all_sections.append(list(unique_symbols))

        return all_sections

    def has_three_different_cards(self, cards: List[str]) -> bool:
        """Check if there are exactly 3 different card symbols"""
        unique_cards = list(set(cards))
        logger.info(f"Checking cards: {cards}, unique: {unique_cards}, count: {len(unique_cards)}")
        return len(unique_cards) == 3

    def is_temporary_message(self, message: str) -> bool:
        """Check if message contains temporary progress emojis"""
        temporary_emojis = ['⏰', '▶', '🕐', '➡️']
        return any(emoji in message for emoji in temporary_emojis)

    def is_final_message(self, message: str) -> bool:
        """Check if message contains final completion emojis"""
        final_emojis = ['✅', '🔰']
        is_final = any(emoji in message for emoji in final_emojis)
        if is_final:
            logger.info(f"🔍 MESSAGE FINAL DÉTECTÉ - Emoji final trouvé dans: {message[:100]}...")
        return is_final

    def get_card_combination(self, cards: List[str]) -> Optional[str]:
        """Get the combination of 3 different cards"""
        unique_cards = list(set(cards))
        if len(unique_cards) == 3:
            combination = ''.join(sorted(unique_cards))
            logger.info(f"Card combination found: {combination} from cards: {unique_cards}")

            # Check if this combination matches any valid pattern
            for valid_combo in VALID_CARD_COMBINATIONS:
                if set(combination) == set(valid_combo):
                    logger.info(f"Valid combination matched: {valid_combo}")
                    return combination

            # Accept any 3 different cards as valid
            logger.info(f"Accepting 3 different cards as valid: {combination}")
            return combination
        return None

    def extract_costumes_from_second_parentheses(self, message: str) -> List[str]:
        """Extract only costumes from exactly 3 cards in the second parentheses"""
        # Find all parentheses content
        pattern = r'\(([^)]+)\)'
        matches = re.findall(pattern, message)
        
        if len(matches) < 2:
            return []
            
        second_parentheses = matches[1]  # Second parentheses (index 1)
        logger.info(f"Deuxième parenthèses contenu: {second_parentheses}")
        
        # Extract only costume symbols (♠️, ♥️, ♦️, ♣️, ❤️)
        costumes = []
        costume_symbols = ["♠️", "♥️", "♦️", "♣️", "❤️"]
        
        # Normalize ❤️ to ♥️ for consistency
        normalized_content = second_parentheses.replace("❤️", "♥️")
        
        # Find all costume symbols in order of appearance
        for char_pos in range(len(normalized_content) - 1):
            two_char_symbol = normalized_content[char_pos:char_pos + 2]
            if two_char_symbol in ["♠️", "♥️", "♦️", "♣️"]:
                costumes.append(two_char_symbol)
        
        logger.info(f"Costumes extraits de la deuxième parenthèse: {costumes}")
        return costumes

    def check_same_costumes_rule(self, costumes: List[str]) -> Optional[str]:
        """
        Check if all 3 costumes are the same and return the predicted costume.
        Rules:
        - ♦️♦️♦️ → predict ♣️ or ♠️ 
        - ♥️♥️♥️ (❤️❤️❤️) → predict ♣️ or ♠️
        - ♣️♣️♣️ → predict ♦️ or ♥️
        - ♠️♠️♠️ → predict ♦️ or ♥️
        """
        if len(costumes) != 3:
            return None
            
        # Check if all costumes are the same
        first_costume = costumes[0]
        if all(costume == first_costume for costume in costumes):
            logger.info(f"🔮 RÈGLE 3 CARTES IDENTIQUES: Toutes les cartes ont le costume {first_costume}")
            
            # Apply the new rules
            if first_costume == "♦️":
                # Choose ♣️ as default prediction for ♦️♦️♦️
                predicted = "♣️"
                logger.info(f"🔮 RÈGLE ♦️♦️♦️ → Prédire {predicted}")
                return predicted
            elif first_costume == "♥️":
                # Choose ♣️ as default prediction for ♥️♥️♥️
                predicted = "♣️"
                logger.info(f"🔮 RÈGLE ♥️♥️♥️ → Prédire {predicted}")
                return predicted
            elif first_costume == "♣️":
                # Choose ♦️ as default prediction for ♣️♣️♣️
                predicted = "♦️"
                logger.info(f"🔮 RÈGLE ♣️♣️♣️ → Prédire {predicted}")
                return predicted
            elif first_costume == "♠️":
                # Choose ♦️ as default prediction for ♠️♠️♠️
                predicted = "♦️"
                logger.info(f"🔮 RÈGLE ♠️♠️♠️ → Prédire {predicted}")
                return predicted
                
        return None

    def can_make_prediction(self) -> bool:
        """Check if enough time has passed since last prediction (70 seconds cooldown)"""
        current_time = time.time()
        
        # Si aucune prédiction n'a été faite encore, autoriser
        if self.last_prediction_time == 0:
            logger.info(f"⏰ PREMIÈRE PRÉDICTION: Aucune prédiction précédente, autorisation accordée")
            return True
            
        time_since_last = current_time - self.last_prediction_time
        
        if time_since_last >= self.prediction_cooldown:
            logger.info(f"⏰ COOLDOWN OK: {time_since_last:.1f}s écoulées depuis dernière prédiction (≥{self.prediction_cooldown}s)")
            return True
        else:
            remaining = self.prediction_cooldown - time_since_last
            logger.info(f"⏰ COOLDOWN ACTIF: Encore {remaining:.1f}s à attendre avant prochaine prédiction")
            return False

    def should_predict(self, message: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        RÈGLES DE PRÉDICTION MISES À JOUR:
        1. Vérification du cooldown de 70 secondes
        2. Règle des 3 cartes identiques (prioritaire)
        3. Règles existantes si pas de cartes identiques
        Returns: (should_predict, game_number, predicted_costume)
        """
        # Extract game number
        game_number = self.extract_game_number(message)
        if not game_number:
            return False, None, None

        logger.debug(f"🔮 PRÉDICTION - Analyse du jeu {game_number}")

        # Check if this is a temporary message (should wait for final edit)
        if self.has_pending_indicators(message) and not self.has_completion_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Message temporaire (⏰▶🕐➡️), attente finalisation")
            self.temporary_messages[game_number] = message
            return False, None, None

        # Skip if we already have a prediction for target game number (+2)
        target_game = game_number + 2
        if target_game in self.predictions and self.predictions[target_game].get('status') == 'pending':
            logger.info(f"🔮 Jeu {game_number}: Prédiction N{target_game} déjà existante, éviter doublon")
            return False, None, None

        # Check if this is a final message (has completion indicators)
        if self.has_completion_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Message final détecté (✅ ou 🔰)")
            # Remove from temporary if it was there
            if game_number in self.temporary_messages:
                del self.temporary_messages[game_number]
                logger.info(f"🔮 Jeu {game_number}: Retiré des messages temporaires")
        
        # Si le message a encore des indicateurs d'attente, ne pas traiter
        elif self.has_pending_indicators(message):
            logger.info(f"🔮 Jeu {game_number}: Encore des indicateurs d'attente, pas de prédiction")
            return False, None, None

        # VÉRIFIER LE COOLDOWN DE 70 SECONDES AVANT TOUTE PRÉDICTION
        if not self.can_make_prediction():
            logger.info(f"🔮 COOLDOWN - Jeu {game_number}: Attente cooldown de {self.prediction_cooldown}s, prédiction différée")
            return False, None, None

        # NOUVELLE RÈGLE: Analyser la deuxième parenthèse pour exactement 3 cartes
        costumes = self.extract_costumes_from_second_parentheses(message)
        
        if len(costumes) != 3:
            logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: Deuxième parenthèse n'a pas exactement 3 cartes ({len(costumes)} costumes trouvés)")
            return False, None, None
            
        logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: 3 costumes extraits: {costumes}")
        
        predicted_costume = None
        
        # RÈGLE PRIORITAIRE: Vérifier si les 3 cartes ont le même costume
        same_costume_prediction = self.check_same_costumes_rule(costumes)
        if same_costume_prediction:
            predicted_costume = same_costume_prediction
            logger.info(f"🔮 RÈGLE 3 IDENTIQUES APPLIQUÉE: {costumes} → Prédire {predicted_costume}")
        else:
            # RÈGLES EXISTANTES: Appliquer les règles basées sur la position et les doublons
            first_costume = costumes[0]
            second_costume = costumes[1] 
            third_costume = costumes[2]
            
            if first_costume == second_costume:
                # Si les deux premières cartes ont le même costume, prendre automatiquement la troisième
                predicted_costume = third_costume
                logger.info(f"🔮 RÈGLE AUTO 1: Les deux premières cartes ont le même costume ({first_costume}) → Prédire automatiquement la troisième carte ({third_costume})")
            elif second_costume == third_costume:
                # NOUVELLE RÈGLE: Si les 2e et 3e cartes ont le même costume, prendre automatiquement la première
                predicted_costume = first_costume
                logger.info(f"🔮 RÈGLE AUTO 2: Les deuxième et troisième cartes ont le même costume ({second_costume}) → Prédire automatiquement la première carte ({first_costume})")
            else:
                # Les trois cartes ont des costumes différents, utiliser la préférence
                if self.position_preference == 1:
                    predicted_costume = first_costume
                    logger.info(f"🔮 RÈGLE POSITION 1: Première carte choisie → Prédire {first_costume}")
                elif self.position_preference == 2:
                    predicted_costume = second_costume
                    logger.info(f"🔮 RÈGLE POSITION 2: Deuxième carte choisie → Prédire {second_costume}")
                else:
                    # Fallback vers la première carte
                    predicted_costume = first_costume
                    logger.info(f"🔮 RÈGLE FALLBACK: Position invalide, utilisation de la première carte → Prédire {first_costume}")
            
        if predicted_costume:
            # Prevent duplicate processing
            message_hash = hash(message)
            if message_hash not in self.processed_messages:
                self.processed_messages.add(message_hash)
                # Mettre à jour le timestamp de la dernière prédiction et sauvegarder
                self.last_prediction_time = time.time()
                self._save_last_prediction_time()
                logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: GÉNÉRATION prédiction pour jeu {target_game} avec costume {predicted_costume}")
                logger.info(f"⏰ COOLDOWN - Prochaine prédiction possible dans {self.prediction_cooldown}s")
                return True, game_number, predicted_costume
            else:
                logger.info(f"🔮 PRÉDICTION - Jeu {game_number}: ⚠️ Déjà traité")
                return False, None, None
                
        return False, None, None

    def make_prediction(self, game_number: int, predicted_costume: str) -> str:
        """Make a prediction for game +2 with the predicted costume"""
        target_game = game_number + 2
        
        # Nouveau format de message de prédiction avec flèche
        prediction_text = f"🔵🇧🇯{target_game}🔵👉🏻:{predicted_costume}statut :⏳"

        # Store the prediction for later verification
        self.predictions[target_game] = {
            'predicted_costume': predicted_costume,
            'status': 'pending',
            'predicted_from': game_number,
            'verification_count': 0,
            'message_text': prediction_text
        }

        logger.info(f"Made prediction for game {target_game} based on costume {predicted_costume}")
        return prediction_text
    
    def get_costume_text(self, costume_emoji: str) -> str:
        """Convert costume emoji to text representation"""
        costume_map = {
            "♠️": "pique",
            "♥️": "coeur", 
            "♦️": "carreau",
            "♣️": "trèfle"
        }
        return costume_map.get(costume_emoji, "inconnu")

    def count_cards_in_winning_parentheses(self, message: str) -> int:
        """Count the number of card symbols in the parentheses that has the ✅ symbol"""
        # Split message at ✅ to find which section won
        if '✅' not in message:
            return 0

        # Find the parentheses after ✅
        checkmark_pos = message.find('✅')
        remaining_text = message[checkmark_pos:]

        # Extract parentheses content after ✅
        pattern = r'\(([^)]+)\)'
        match = re.search(pattern, remaining_text)

        if match:
            winning_content 
