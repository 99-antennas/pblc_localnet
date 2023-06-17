import spacy

class NERAnalyzer:
    def __init__(self, model='en_core_web_sm'):
        self.nlp = spacy.load(model)
    
    def analyze_text(self, text):
        doc = self.nlp(text)
        entities = []
        
        for entity in doc.ents:
            entities.append({
                'text': entity.text,
                'label': entity.label_
            })
        
        return entities