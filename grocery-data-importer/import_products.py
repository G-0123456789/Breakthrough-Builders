import os
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase Admin SDK
credential_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "service-account.json")

if not os.path.exists(credential_path):
    raise RuntimeError(f"Service account credential file '{credential_path}' not found.")

cred = credentials.Certificate(credential_path)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Complete South African Grocery Seed Dataset with all required fields (name, title, nameSearch, isActive, etc.)
SAMPLE_PRODUCTS = [
    ("prod_1", {
        "id": "prod_1",
        "name": "PnP Live Well Maize Meal 10kg",
        "title": "PnP Live Well Maize Meal 10kg",
        "nameSearch": "pnp live well maize meal 10kg",
        "brand": "PnP",
        "category": "Pantry",
        "size": "10kg",
        "barcode": "6001000123456",
        "isEssential": True,
        "lowestPrice": 119.99,
        "nearestStoreName": "PnP",
        "storeBadge": "PnP",
        "saveBadge": "SAVE",
        "comboText": "Combo For R299.00",
        "isActive": True
    }),
    ("prod_2", {
        "id": "prod_2",
        "name": "Superior White Bread 700g",
        "title": "Superior White Bread 700g",
        "nameSearch": "superior white bread 700g",
        "brand": "Albany",
        "category": "Bakery",
        "size": "700g",
        "barcode": "6001000234567",
        "isEssential": True,
        "lowestPrice": 17.99,
        "nearestStoreName": "Pick n Pay",
        "storeBadge": "PnP",
        "saveBadge": "SAVE",
        "comboText": "Buy 2 For R30.00",
        "isActive": True
    }),
    ("prod_3", {
        "id": "prod_3",
        "name": "Instant Coffee 200g",
        "title": "Instant Coffee 200g",
        "nameSearch": "instant coffee 200g",
        "brand": "Ricoffy",
        "category": "Pantry",
        "size": "200g",
        "barcode": "6001000345678",
        "isEssential": True,
        "lowestPrice": 44.99,
        "nearestStoreName": "Shoprite",
        "storeBadge": "Shoprite",
        "saveBadge": "SAVE",
        "comboText": "",
        "isActive": True
    }),
    ("prod_4", {
        "id": "prod_4",
        "name": "Sunflower Oil 2L",
        "title": "Sunflower Oil 2L",
        "nameSearch": "sunflower oil 2l",
        "brand": "Excella",
        "category": "Pantry",
        "size": "2L",
        "barcode": "6001000456789",
        "isEssential": True,
        "lowestPrice": 69.99,
        "nearestStoreName": "Checkers",
        "storeBadge": "Checkers",
        "saveBadge": "SAVE",
        "comboText": "Special Deal",
        "isActive": True
    }),
    ("prod_5", {
        "id": "prod_5",
        "name": "Large Eggs 30s",
        "title": "Large Eggs 30s",
        "nameSearch": "large eggs 30s",
        "brand": "Nulaid",
        "category": "Dairy",
        "size": "30 pack",
        "barcode": "6001000567890",
        "isEssential": True,
        "lowestPrice": 89.99,
        "nearestStoreName": "Spar",
        "storeBadge": "SPAR",
        "saveBadge": "SAVE",
        "comboText": "",
        "isActive": True
    }),
    ("prod_6", {
        "id": "prod_6",
        "name": "Basmati Rice 2kg",
        "title": "Basmati Rice 2kg",
        "nameSearch": "basmati rice 2kg",
        "brand": "Tastic",
        "category": "Pantry",
        "size": "2kg",
        "barcode": "6001000678901",
        "isEssential": False,
        "lowestPrice": 54.99,
        "nearestStoreName": "Pick n Pay",
        "storeBadge": "PnP",
        "saveBadge": "SAVE",
        "comboText": "",
        "isActive": True
    }),
    ("prod_7", {
        "id": "prod_7",
        "name": "Cheddar Cheese 800g",
        "title": "Cheddar Cheese 800g",
        "nameSearch": "cheddar cheese 800g",
        "brand": "Melrose",
        "category": "Dairy",
        "size": "800g",
        "barcode": "6001000789012",
        "isEssential": False,
        "lowestPrice": 109.99,
        "nearestStoreName": "Woolworths",
        "storeBadge": "Woolies",
        "saveBadge": "SAVE",
        "comboText": "",
        "isActive": True
    })
]

SAMPLE_OFFERS = [
    ("off_1", {"id": "off_1", "productId": "prod_1", "storeId": "checkers", "provinceCode": "FS", "price": 119.99, "currency": "ZAR", "isPromotion": True, "promotionPrice": 109.99, "isActive": True}),
    ("off_2", {"id": "off_2", "productId": "prod_2", "storeId": "picknpay", "provinceCode": "FS", "price": 17.99, "currency": "ZAR", "isPromotion": True, "promotionPrice": 15.99, "isActive": True}),
    ("off_3", {"id": "off_3", "productId": "prod_3", "storeId": "shoprite", "provinceCode": "FS", "price": 44.99, "currency": "ZAR", "isPromotion": False, "promotionPrice": None, "isActive": True}),
    ("off_4", {"id": "off_4", "productId": "prod_4", "storeId": "checkers", "provinceCode": "FS", "price": 69.99, "currency": "ZAR", "isPromotion": True, "promotionPrice": 64.99, "isActive": True})
]

def import_records(products, offers):
    """
    products: iterable of (stable_product_id, document)
    offers: iterable of (stable_offer_id, document)
    """
    batch = db.batch()
    count = 0

    for product_id, product in products:
        ref = db.collection("products").document(product_id)
        batch.set(ref, product, merge=True)
        count += 1

        if count >= 400:
            batch.commit()
            batch = db.batch()
            count = 0

    for offer_id, offer in offers:
        ref = db.collection("offers").document(offer_id)
        batch.set(ref, offer, merge=True)
        count += 1

        if count >= 400:
            batch.commit()
            batch = db.batch()
            count = 0

    if count:
        batch.commit()


if __name__ == "__main__":
    print("Importing dataset into Cloud Firestore...")
    import_records(products=SAMPLE_PRODUCTS, offers=SAMPLE_OFFERS)
    print("Import completed successfully!")
