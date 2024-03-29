import random
import json
import pickle
import numpy as np
import nltk

nltk.download('punkt')
nltk.download('wordnet')
from nltk import WordNetLemmatizer
from .message import message_dict

from tensorflow.keras.models import load_model

lemmatizer = WordNetLemmatizer()
intents = json.loads(open('./response_to_user/intents.json').read())

words = pickle.load(open('./response_to_user/words.pkl', 'rb'))
classes = pickle.load(open('./response_to_user/classes.pkl', 'rb'))
model = load_model('./response_to_user/chatbot_model.h5')


def clean_up_sentence(sentence):
  sentence_words = nltk.word_tokenize(sentence)
  sentence_words = [lemmatizer.lemmatize(word) for word in sentence_words]
  return sentence_words


def bag_of_words(sentence):
  sentence_words = clean_up_sentence(sentence)
  bag = [0] * len(words)
  for w in sentence_words:
    for i, word in enumerate(words):
      if word == w:
        bag[i] = 1
  return np.array(bag)


def predict_class(sentence):
  bow = bag_of_words(sentence)
  res = model.predict(np.array([bow]), verbose=0)[0]
  ERROR_THRESHOLD = 0.25
  results = [[i, r] for i, r in enumerate(res) if r > ERROR_THRESHOLD]

  results.sort(key=lambda x: x[1], reverse=True)
  return_list = []
  for r in results:
    return_list.append({'intent': classes[r[0]], 'probalility': str(r[1])})
  return return_list


def get_response(message):
  if message.lower() in message_dict:
    return message_dict[message.lower()]
  else:
    intents_list = predict_class(message.lower())
    tag = intents_list[0]['intent']
    list_of_intents = intents['intents']
    for i in list_of_intents:
      if i['tag'] == tag:
        result = random.choice(i['responses'])
    return result


print('________GOOOO___________')
