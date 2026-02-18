import random

class TextAugmenter:

    def __init__(self, prob=0.2, seed=None):
        self.prob = prob
        if seed is not None:
            random.seed(seed)

    def random_deletion(self, words):
        if len(words) <= 2:
            return words

        new_words = [w for w in words if random.random() > self.prob]

        while len(new_words) < 2:
            new_words.append(random.choice(words))

        return new_words

    def random_swap(self, words, n=2):
        words = words[:]
        for _ in range(n):
            if len(words) < 2:
                break
            i, j = random.sample(range(len(words)), 2)
            words[i], words[j] = words[j], words[i]
        return words

    def typo_noise(self, word):
        if len(word) < 3:
            return word
        i = random.randint(0, len(word)-2)
        return word[:i] + word[i+1] + word[i] + word[i+2:]

    def inject_noise(self, words):
        return [
            self.typo_noise(w) if random.random() < self.prob else w
            for w in words
        ]

    def augment(self, text: str) -> str:
        words = text.split()

        ops = [
            self.random_deletion,
            self.random_swap,
            self.inject_noise
        ]

        op = random.choice(ops)
        return " ".join(op(words))
