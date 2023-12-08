from firebase_admin import messaging

# Fonction pour envoyer une notification avec Firebase Admin
def send_notification(transaction):
    print(transaction)
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title='Madis',
                body=f'Le statut de votre transaction {transaction.reference} est maintenant {transaction.status}.'
            ),
        android=messaging.AndroidConfig(
  
        priority='normal',
        notification=messaging.AndroidNotification(
           
            icon='stock_ticker_update',
            color='#f45342',
      image='https://www.pngitem.com/pimgs/m/359-3590778_image-of-pizza-monster-sticker-pizza-monster-png.png',
      
        ),
    ),
            data={
                "title":"Etat de la transaction",
                "message":f'Le statut de votre transaction {transaction.reference} est maintenant {transaction.status}.'
            },
            token=transaction.transaction_token,  # Remplacez par le vrai token du dispositif
        )

        # Envoyer le message
        response = messaging.send(message)
        print('Notification sent successfully:', response)
    except Exception as e:
        print('Error sending notification:', str(e))
