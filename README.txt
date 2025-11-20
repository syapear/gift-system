GiftHub + KeyReceiver System

1. Deploy server to Railway/Render.
2. Set env var GIFT_HUB_TOKEN=nezusystemde
3. Run key_receiver.py on each client PC.
4. TikFinity sends gift events to:
   https://YOUR_APP_URL/gift?token=nezusystemde&key=v&duration_ms=50
