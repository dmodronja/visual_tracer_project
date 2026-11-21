## VISUAL TRACER PROJECT

## Descrizione
Questo progetto permette di ottenere la posizione di hostname e IP in Internet.
È basato su un server locale flask che espone su porta 5000 una mappa (interfaccia grafica).
Uno script python avvia il server ed effettua il tracciamento verso il sito cercato.
Si appoggia al database GeoLite di MaxMind (scaricato in automatico) per trovare la città corrispondente all'indirizzo cercato.
# Si consiglia di eliminare ogni settimana il database, poiché viene scaricato ad ogni avvio la copia aggiornata.

## Avvio
Eseguire il file 'start.bat'.

## Arresto
Chiudere il processo attivo di 'start.bat' e la finestra del browser aperta.

## Utilizzo
All'avvio, dopo la configurazione e il download del database appare la pagina del server flask.
Inserire l'indirizzo da cercare nell'apposita casella di ricerca e attendere circa 7 minuti per la comparsa dei risultati.
# Se sono impostate le coordinate nel file 'user/user.config' il programma mostrerà il percorso completo a partire da quella posizione fino al sito, includendo i passaggi intermedi del tracciamento.
