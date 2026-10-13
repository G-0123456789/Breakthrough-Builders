import os
import firebase_admin
from firebase_admin import credentials, firestore

# Set GOOGLE_APPLICATION_CREDENTIALS to the path
# of your downloaded service-account JSON file.
credential_path = os.environ.get(
    "GOOGLE_APPLICATION_CREDENTIALS"
)

if not credential_path:
    raise RuntimeError(
        "Set GOOGLE_APPLICATION_CREDENTIALS first."
    )

cred = credentials.Certificate(credential_path)
firebase_admin.initialize_app(cred)

db = firestore.client()


def import_records(products, offers):
    """
    products: iterable of (stable_product_id, document)
    offers: iterable of (stable_offer_id, document)

    Map the real API response into these records first.
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
    # Replace these empty lists with validated API data.
    # Do not import sample or invented prices as real offers.
    import_records(products=[], offers=[])
    print("Import completed.")
