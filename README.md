# Wallabot
A chatbot expert in second-hand item price negotiation based on fuzzy logic.

This project is a proof of concept designed for a class assigment for the IDIF subject (Modelling with uncertainity, fuzzy logic and soft computing) within the [TECI Master degree](https://blogs.mat.ucm.es/teci/) from Polytechnic University of Madrid and the Complutense University of Madrid. For this reason, although the documentation are code are in english, the interface and prompts are written in spanish. Sorry for the inconvenience!

![Chat UI](img/chat_UI.png)
![Control Panel](img/control_panel.png)
![Membership Functions](img/membership_functions.png)

legal disclaimer: The purpose of this project is purely academic and educational. Wallabot no tiene ninguna relación, afiliación ni patrocinio de Wallapop S.L.

## Set Up

1. Create a ``.env`` file following the structure in ``example.env`` and add your OpenAI API token. If you don't have one you can easily create one [here](https://developers.openai.com/api/docs/quickstart).

2. Run the app with uv:
```
uv run streamlit run main.py
```
3. Access the app in http://localhost:8501 and enjoy negotiating 🥸$$.

## Bot's behaviour explainer

The chatbot's behaviour is controlled by fuzzy logic.

Fuzzy inputs:
- Conversation duration: The number of user-bot interactions.
- User's tone (friendly, neutral or agressive). I use a zero shot text classification model ([bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)) to compute the probability distribution for each of the 3 classes and then compute the score with the functoin Tono = 0 x P(“Friendly”) + 5 x P(“Neutral”) + 10 x P(“Agressive). Thus, 0 indicates friendly tone and values closer to 10 indicate more agressive tone.
- Price: Simply extracted from the user's message using regular expressions.

Fuzzy outputs:

The fuzzy output is the ddegree of acceptance. Depending on the degree of acceptance one strategy or another will be selected and inyected in the system prompt.

- Very high: Accept offer
- High: Counteroffer
- Low: Mantain the price
- Verly low: Reject offer and end negotiating 


Rules:
I defined the rules following well known negotiationg principles from works such as how to make friends and influence people from Dale Carneige such as "Nunca recompenses la agresividad con concesiones.", "Buena fe y búsqueda de beneficio mutuo". The following table shows the 17 rules I defined.


| Tono del Comprador | Diferencia Relativa de Precio | Duración de Negociación | Acción |
|---------------------|------------------------------|-----------------------------------------|-----|
| Amigable           | Baja                         | Corta                                   | Aceptar |
| Amigable           | Baja                         | Media                                   | Aceptar |
| Amigable           | Baja                         | Larga                                   | Contraoferta |
| Amigable           | Media                        | Corta                                   | Contraoferta |
| Amigable           | Media                        | Media                                   | Contraoferta |
| Amigable           | Media                        | Larga                                   | Mantener |
| Amigable           | Alta                         | Corta                                   | Contraoferta |
| Amigable           | Alta                         | Media                                   | Mantener |
| Amigable           | Alta                         | Larga                                   | Rechazar |
| Neutral            | Baja                         | Corta                                   | Aceptar |
| Neutral            | Baja                         | Media                                   | Aceptar |
| Neutral            | Baja                         | Larga                                   | Contraoferta |
| Neutral            | Media                        | Corta                                   | Contraoferta |
| Neutral            | Media                        | Media                                   | Mantener |
| Neutral            | Media                        | Larga                                   | Mantener |
| Neutral            | Alta                         | Corta                                   | Mantener |
| Neutral            | Alta                         | Media                                   | Mantener |
| Neutral            | Alta                         | Larga                                   | Mantener |
| Agresivo           | Baja                         | Corta                                   | Mantener |
| Agresivo           | Baja                         | Media                                   | Mantener |
| Agresivo           | Baja                         | Larga                                   | Rechazar |
| Agresivo           | Media                        | Corta                                   | Mantener |
| Agresivo           | Media                        | Media                                   | Mantener |
| Agresivo           | Media                        | Larga                                   | Rechazar |
| Agresivo           | Alta                         | Corta                                   | Rechazar |
| Agresivo           | Alta                         | Media                                   | Rechazar |
| Agresivo           | Alta                         | Larga                                   | Rechazar |


to do idif
- repasar la documentación, dejarla bien escrita y bonita
- licencia
- cambiar nombre por wallabot