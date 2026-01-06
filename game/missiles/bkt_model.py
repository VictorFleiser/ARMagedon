"""
Bayesian Knowledge Tracing (BKT) model for tracking user knowledge of letters.

BKT Parameters:
- P(L0): Initial probability of knowing the letter (default 0)
- P(T): Probability of learning/transitioning from not-knowing to knowing
- P(S): Slip probability (correct response despite not knowing)
- P(G): Guess probability (incorrect response despite knowing)
- P(K): Current probability of knowing the letter (updated dynamically)
"""
import math

class BKTModel:
	def __init__(
		self,
		letters,
		initial_number_of_letters_tested,
		p_l0=0.0,
		p_t=0.1,
		p_s=0.1,
		p_g=0.25,
		base_decay_rate=0.03,
		stability_factor=0.5
	):
		self.letters = letters
		self.number_of_letters_tested = initial_number_of_letters_tested
		self.p_l0 = p_l0
		self.p_t = p_t
		self.p_s = p_s
		self.p_g = p_g
		self.base_decay_rate = base_decay_rate
		self.stability_factor = stability_factor
		
		# Initialize knowledge probability for each letter
		self.p_k = {letter: p_l0 for letter in letters}

		self.success_score = {letter: 0 for letter in letters}
	
	def update_correct(self, letter):
		if letter not in self.p_k:
			return
		
		p_k_prev = self.p_k[letter]
		
		# P(K | correct) (Th de Bayes)
		# P(correct | K) = 1 - P(S)
		# P(correct | ~K) = P(G)
		p_correct_given_k = 1 - self.p_s
		p_correct_given_not_k = self.p_g
		
		# P(correct) = P(correct | K) * P(K) + P(correct | ~K) * P(~K)
		p_correct = (p_correct_given_k * p_k_prev + 
					p_correct_given_not_k * (1 - p_k_prev))
		
		# P(K | correct) = P(correct | K) * P(K) / P(correct)
		if p_correct > 0:
			p_k_after_evidence = (p_correct_given_k * p_k_prev) / p_correct
		else:
			p_k_after_evidence = p_k_prev
		
		# learning: P(K) = P(K | correct) + (1 - P(K | correct)) * P(T)
		self.p_k[letter] = p_k_after_evidence + (1 - p_k_after_evidence) * self.p_t
		self.p_k[letter] = max(0.0, min(1.0, self.p_k[letter]))

		self.success_score[letter] += 1
	
	def update_incorrect(self, letter):
		if letter not in self.p_k:
			return
		
		p_k_prev = self.p_k[letter]
		
		# P(K | incorrect) (Th de Bayes)
		# P(incorrect | K) = P(S)
		# P(incorrect | ~K) = 1 - P(G)
		p_incorrect_given_k = self.p_s
		p_incorrect_given_not_k = 1 - self.p_g
		
		# P(incorrect) = P(incorrect | K) * P(K) + P(incorrect | ~K) * P(~K)
		p_incorrect = (p_incorrect_given_k * p_k_prev + 
					  p_incorrect_given_not_k * (1 - p_k_prev))
		
		# P(K | incorrect) = P(incorrect | K) * P(K) / P(incorrect)
		if p_incorrect > 0:
			p_k_after_evidence = (p_incorrect_given_k * p_k_prev) / p_incorrect
		else:
			p_k_after_evidence = p_k_prev
		
		# learning: P(K) = P(K | incorrect) + (1 - P(K | incorrect)) * P(T)
		self.p_k[letter] = p_k_after_evidence + (1 - p_k_after_evidence) * self.p_t
		self.p_k[letter] = max(0.0, min(1.0, self.p_k[letter]))

		self.success_score[letter] = max(0, self.success_score[letter] // 2)
	
	
	def update_decay(self, dt):
		""" Adaptive exponential decay """
		for letter in self.letters[:self.number_of_letters_tested]:
			# Calculate dynamic decay rate based on stability
			# rate = base / (1 + factor * success_count)
			stability = self.success_score.get(letter, 0)

			effective_decay = self.base_decay_rate / (1.0 + (self.stability_factor * stability))
			# Example with base=0.05, factor=0.5:
			# 0 successes: rate = 0.05 (Fast)
			# 1 success:   rate = 0.033
			# 5 successes: rate = 0.014 (Slow)

			decay_multiplier = math.exp(-effective_decay * dt)
			self.p_k[letter] = self.p_k[letter] * decay_multiplier

	
	def get_knowledge(self, letter):
		return self.p_k.get(letter, self.p_l0)
	
	def get_all_knowledge(self, all_letters=False):
		# all_letters: if True, return knowledge for all letters, else only for tested letters
		if all_letters:
			return dict(self.p_k)
		else:
			return {letter: self.p_k[letter] for letter in self.letters[:self.number_of_letters_tested]}
	
	def get_weakest_letters(self, n=5, all_letters=False):
		# Return n letters with lowest P(K)
		# if all_letters is True, consider all letters, else only tested letters
		if all_letters:
			sorted_letters = sorted(self.p_k.items(), key=lambda x: x[1])
		else:
			sorted_letters = sorted(
				{letter: self.p_k[letter] for letter in self.letters[:self.number_of_letters_tested]}.items(),
				key=lambda x: x[1]
			)
		return sorted_letters[:n]
	
	def get_strongest_letters(self, n=5, all_letters=False):
		if all_letters:
			sorted_letters = sorted(self.p_k.items(), key=lambda x: x[1], reverse=True)
		else:
			sorted_letters = sorted(
				{letter: self.p_k[letter] for letter in self.letters[:self.number_of_letters_tested]}.items(),
				key=lambda x: x[1],
				reverse=True
			)
		return sorted_letters[:n]
	
	def get_lowest_overall_knowledge(self, all_letters=False):
		if all_letters:
			knowledge_values = self.p_k.values()
		else:
			knowledge_values = [self.p_k[letter] for letter in self.letters[:self.number_of_letters_tested]]
		
		if not knowledge_values:
			return 0.0
		
		# return sum(knowledge_values) / len(knowledge_values)
		return min(knowledge_values)