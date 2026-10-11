import json
import unittest

from app import _parse_product_page


_MISSING = object()


def _product_html(
    pdp_data=None,
    *,
    offer_price=9999,
    availability=_MISSING,
    visible_text="",
):
    scripts = []
    if pdp_data is not None:
        payload = {"pageName": "pdp", "pdpData": pdp_data}
        scripts.append(f"<script>window.__myx = {json.dumps(payload)};</script>")

    offer = {"@type": "Offer", "price": offer_price}
    if availability is not _MISSING:
        offer["availability"] = availability
    ld_product = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": "Fixture product",
        "offers": offer,
    }
    scripts.append(
        '<script type="application/ld+json">'
        f"{json.dumps(ld_product)}"
        "</script>"
    )
    return f"<html><head>{''.join(scripts)}</head><body>{visible_text}</body></html>"


def _size(label, available, *, count=None, discounted_price=None):
    seller_data = []
    if count is not None or discounted_price is not None:
        seller = {}
        if count is not None:
            seller["sellableInventoryCount"] = count
            seller["availableCount"] = count
        if discounted_price is not None:
            seller["discountedPrice"] = discounted_price
        seller_data.append(seller)
    return {
        "label": label,
        "available": available,
        "sizeSellerData": seller_data,
    }


class ProductParserStockAndPriceTests(unittest.TestCase):
    def parse(self, html):
        return _parse_product_page(html, "https://www.myntra.com/123", "123")

    def test_in_stock_discounted_price_uses_pdp_data_over_ld_mrp(self):
        pdp_data = {
            "mrp": 2999,
            "price": {"mrp": 2999, "discounted": 924},
            "sizes": [_size("M", True, count=5, discounted_price=924)],
        }

        product = self.parse(_product_html(pdp_data, offer_price=2999))

        self.assertEqual(product["stock_availability"], "In Stock")
        self.assertEqual(product["current_price"], 924)
        self.assertEqual(product["original_price"], 2999)

    def test_in_stock_full_mrp_price_is_retained(self):
        pdp_data = {
            "mrp": 2999,
            "price": {"mrp": 2999, "discounted": 2999},
            "sizes": [_size("One Size", True, count=2, discounted_price=2999)],
        }

        product = self.parse(_product_html(pdp_data, offer_price=2999))

        self.assertEqual(product["stock_availability"], "In Stock")
        self.assertEqual(product["current_price"], 2999)

    def test_all_sizes_unavailable_zeroes_mrp_placeholder(self):
        pdp_data = {
            "mrp": 4499,
            "price": {"mrp": 4499, "discounted": 4499},
            "discountDisplayLabel": "(50% OFF)",
            "sizes": [
                _size("S", False),
                _size("M", False, count=0, discounted_price=4499),
            ],
        }

        product = self.parse(_product_html(pdp_data, offer_price=4499))

        self.assertEqual(product["stock_availability"], "Out of Stock")
        self.assertEqual(product["current_price"], 0)
        self.assertIsInstance(product["current_price"], int)
        self.assertEqual(product["original_price"], 4499)
        self.assertEqual(product["discount"], "")

    def test_one_sellable_size_makes_product_in_stock(self):
        pdp_data = {
            "mrp": 1999,
            "price": {"mrp": 1999, "discounted": 1299},
            "sizes": [
                _size("S", False, count=0),
                _size("M", True, count=3, discounted_price=1299),
            ],
        }

        product = self.parse(_product_html(pdp_data, offer_price=1999))

        self.assertEqual(product["stock_availability"], "In Stock")
        self.assertEqual(product["current_price"], 1299)

    def test_missing_stock_signal_is_unknown_and_price_is_zero(self):
        product = self.parse(_product_html(offer_price=4499))

        self.assertEqual(product["stock_availability"], "Unknown")
        self.assertEqual(product["current_price"], 0)

    def test_ld_json_is_used_when_pdp_inventory_is_unavailable(self):
        product = self.parse(
            _product_html(
                offer_price=1299,
                availability="https://schema.org/InStock",
            )
        )

        self.assertEqual(product["stock_availability"], "In Stock")
        self.assertEqual(product["current_price"], 1299)

    def test_visible_sold_out_text_is_a_fallback(self):
        product = self.parse(
            _product_html(
                offer_price=2499,
                visible_text="This product is currently sold out",
            )
        )

        self.assertEqual(product["stock_availability"], "Out of Stock")
        self.assertEqual(product["current_price"], 0)


if __name__ == "__main__":
    unittest.main()
