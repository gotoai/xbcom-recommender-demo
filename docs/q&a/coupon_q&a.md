# Inbound-traveler coupon Q&A

Example traveler questions and concierge answers about the coupons, grounded in the
app's data model: nearest-first active coupons within 5 km of the traveler's current
location, each with a discount (percentage or fixed yen), validity window, price, and
code. Drafted in English to match the user (traveler) view.

---

## A. Finding & understanding coupons

**1. Q: What are these coupons?**
A: They're discounts at shops near where you are right now in Tokyo. We show every offer that's active today within 5 km of your current location, closest first.

**2. Q: How were these picked for me?**
A: (In the case no other filter conditions are applied) By your live location — the map centers on where you are during this time of day, and we search a 5 km radius. The list is sorted by walking-ish distance, nearest at the top.

**3. Q: Why do I see different coupons than my friend?**
A: Because the search is based on each person's current location. If you're in Shibuya and they're in Taito, you'll see different nearby shops.

**4. Q: The list changed since this morning — why?**
A: Your location updates through the day, and it is refreshed with the systame with a candence. As you move, the 5 km search moves with you, so the nearby coupons refresh.

**5. Q: How many coupons are near me?**
A: The header shows the total within 5 km (e.g., "1,959 within 5 km"). The list pages through them 5 at a time; the map plots the nearest 200 as pins.

**6. Q: What does the number after the shop mean?**
A: The 📍 chip is the straight-line distance from your current location to that shop, in kilometers.

## B. Discounts & price

**7. Q: How big is the discount?**
A: Each coupon shows it on the orange chip — either a percentage (e.g., "5% OFF") or a fixed amount (e.g., "¥80 OFF").

**8. Q: Is "¥1,200" the price before or after the discount?**
A: That's the regular product price. Apply the coupon's discount to it — so "¥1,200" with "¥80 OFF" comes to ¥1,120.

**9. Q: What's the biggest discount available near me?**
A: Sort/scan the list — discounts range from a few percent up to about 30% on some items. The exact best offer depends on what's within your 5 km right now.

**10. Q: Are the prices in yen? Do they include tax?**
A: Yes, all prices are Japanese yen (¥). Treat them as the listed shelf price; confirm tax handling at the shop.

**11. Q: Can I combine two coupons?**
A: Each coupon is a single offer for one product at one shop. Assume one coupon per item unless the shop says otherwise.

## C. Redeeming

**12. Q: How do I use a coupon?**
A: Show the coupon (its code) to the shop at checkout. Each coupon has a unique code tied to that offer.

**13. Q: Do I need to book or reserve first?**
A: No reservation is needed to hold the coupon — just present it in-store within its valid dates.

**14. Q: Is there a code I show at the register?**
A: Yes, every coupon carries a code. That's what the shop uses to apply the discount.

**15. Q: Can I use the same coupon twice?**
A: Treat each as single-use per traveler. Once redeemed, consider it spent.

**16. Q: Do I redeem in the app or at the shop?**
A: At the shop. This screen helps you discover and navigate to offers; the discount is applied in person.

## D. Validity & timing

**17. Q: Until when is this coupon valid?**
A: Each card shows "Until MM-DD" — that's the last day it's active. Only coupons valid today appear in your list.

**18. Q: I see "Until MM-DD" — assume MM-DD is today's date, can I still use it today?**
A: Yes. The end date is inclusive, so a coupon ending today is still valid today.

**19. Q: Will these coupons still be here tomorrow?**
A: Some will expire and new ones will become active. The list only ever shows what's valid on the current day, so check again tomorrow.

**20. Q: Are coupons tied to a time of day?**
A: The coupons are valid for the whole day within their date window. You might see different coupons in the list when you move, but the coupon's validity doesn't change.

## E. Location & navigation

**21. Q: Where am I on the map?**
A: The blue dot at the center labeled "You are here" is your current location; the shaded circle is the 5 km search area.

**22. Q: How far can a coupon be?**
A: Up to 5 km from your current spot. Anything farther isn't shown.

**23. Q: How do I get to the shop?**
A: Tap the shop's pin on the map to see its name and distance, then use the map to navigate toward it.

**24. Q: The map labels are in English — is that everywhere?**
A: In this traveler view everything is English, including the map's place labels, so you can read street and station names easily.

**25. Q: Why are all the shops in central Tokyo?**
A: The participating shops are concentrated in the central wards (Minato, Shibuya, Shinjuku, Taito, Chiyoda, Chuo). If you're in an outer ward, you may see few or none within 5 km.

**26. Q: I see "No active coupons within 5 km" — what now?**
A: You're likely outside the central shop area right now. Head toward a central ward (or check back later when your location updates) and offers will appear.

## F. Categories & tourist practicalities

**27. Q: Can I filter to just food, or just shopping?**
A: Category isn't filterable yet in this view — but each card shows its category (Restaurant, Bar, Sweets Shop, Clothing, etc.) and an icon, so you can scan quickly.

**28. Q: What kinds of shops offer coupons?**
A: A broad mix — restaurants, bars, cafés, fast food, sweets, clothing, drugstores, electronics, karaoke, spas, gyms, massage, bookstores, car rental, luggage storage, and more.

**29. Q: I don't eat pork / I have allergies — is that shown?**
A: The coupon lists the product and shop but not full ingredient info. Please confirm dietary details directly with the shop before ordering.

**30. Q: Can the concierge recommend the best coupon for me?**
A: That's coming soon — the chat assistant will suggest offers based on your interests and location. For now, the nearest-first list and the map are your guide.
