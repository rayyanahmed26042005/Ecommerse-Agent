"""Static catalog endpoints for sidebar (trending, essentials, picks)."""

from app.models.schemas import ProductSuggestion, Retailer

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?q=80&w=1200&auto=format&fit=crop"


def get_trending() -> list[ProductSuggestion]:
    return [
        ProductSuggestion(
            title="Aurora Pro Wireless Earbuds",
            category="Audio",
            price=129,
            rating=4.7,
            image="https://images.unsplash.com/photo-1518443895914-06e0f2eeaad6?q=80&w=1200&auto=format&fit=crop",
            specs=["ANC", "Bluetooth 5.3"],
            retailers=[Retailer(name="Amazon", price=129, best=True)],
        ),
        ProductSuggestion(
            title="ASUS 24\" 144Hz Monitor",
            category="Monitors",
            price=179,
            rating=4.6,
            image="https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?q=80&w=1200&auto=format&fit=crop",
            specs=["1080p", "1ms", "IPS"],
            retailers=[Retailer(name="Amazon", price=179, best=True)],
        ),
        ProductSuggestion(
            title="iBUYPOWER Gaming PC",
            category="Gaming",
            price=449,
            rating=4.2,
            image="https://images.unsplash.com/photo-1587202372775-e229f172b9a7?q=80&w=1200&auto=format&fit=crop",
            specs=["Ryzen 5", "GTX 1660", "16GB RAM"],
            retailers=[Retailer(name="Amazon", price=449, best=True)],
        ),
        ProductSuggestion(
            title="Nimbus Lite Vacuum",
            category="Home",
            price=179,
            rating=4.5,
            image="https://images.unsplash.com/photo-1581578731548-c64695cc6952?q=80&w=1200&auto=format&fit=crop",
            specs=["HEPA", "Cordless"],
            retailers=[Retailer(name="Target", price=179, best=True)],
        ),
    ]


def get_essentials() -> list[ProductSuggestion]:
    return [
        ProductSuggestion(
            title="Luma Desk Lamp",
            category="Office",
            price=89,
            rating=4.6,
            image="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?q=80&w=1200&auto=format&fit=crop",
            retailers=[Retailer(name="Ikea", price=89, best=True)],
        ),
        ProductSuggestion(
            title="Voyage Travel Kit",
            category="Travel",
            price=49,
            rating=4.4,
            image="https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop",
            retailers=[Retailer(name="Amazon", price=49, best=True)],
        ),
        ProductSuggestion(
            title="Ergo Chair Lite",
            category="Office",
            price=199,
            rating=4.3,
            image="https://images.unsplash.com/photo-1580480057503-bf9a8a6f0b08?q=80&w=1200&auto=format&fit=crop",
            retailers=[Retailer(name="Amazon", price=199, best=True)],
        ),
        ProductSuggestion(
            title="USB-C Hub Pro",
            category="Accessories",
            price=39,
            rating=4.5,
            image=DEFAULT_IMAGE,
            retailers=[Retailer(name="Amazon", price=39, best=True)],
        ),
    ]


def get_personal_picks(user_id: str) -> list[ProductSuggestion]:
    _ = user_id
    return [
        ProductSuggestion(
            title="Minimal Webcam HD",
            category="Office",
            price=59,
            rating=4.4,
            image=DEFAULT_IMAGE,
            retailers=[Retailer(name="Amazon", price=59, best=True)],
        ),
        ProductSuggestion(
            title="Ergo Chair Lite",
            category="Office",
            price=199,
            rating=4.3,
            image="https://images.unsplash.com/photo-1580480057503-bf9a8a6f0b08?q=80&w=1200&auto=format&fit=crop",
            retailers=[Retailer(name="Amazon", price=199, best=True)],
        ),
    ]
