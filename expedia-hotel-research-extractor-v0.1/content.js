(() => {
  if (window.__expediaHotelExtractorLoaded) return;
  window.__expediaHotelExtractorLoaded = true;

  const clean = value => (value || "").replace(/\s+/g, " ").trim();

  function text(selector) {
    const el = document.querySelector(selector);
    return clean(el?.textContent);
  }

  function firstNonEmpty(values) {
    return values.map(clean).find(Boolean) || "";
  }

  function meta(name) {
    const el = document.querySelector(`meta[name="${name}"], meta[property="${name}"]`);
    return clean(el?.content);
  }

  function jsonLdObjects() {
    const out = [];
    for (const script of document.querySelectorAll('script[type="application/ld+json"]')) {
      try {
        const parsed = JSON.parse(script.textContent);
        if (Array.isArray(parsed)) out.push(...parsed);
        else if (parsed && parsed["@graph"]) out.push(...parsed["@graph"]);
        else if (parsed) out.push(parsed);
      } catch {}
    }
    return out;
  }

  function findHotelLd() {
    return jsonLdObjects().find(x => {
      const t = x?.["@type"];
      return t === "Hotel" || t === "LodgingBusiness" ||
             (Array.isArray(t) && t.some(v => /hotel|lodging/i.test(v)));
    }) || null;
  }

  function allVisibleText() {
    return clean(document.body?.innerText || "");
  }

  function collectAmenities() {
    const labels = new Set();
    const keywords = [
      "free wifi", "wifi", "pool", "parking", "breakfast", "restaurant",
      "bar", "gym", "fitness", "spa", "air conditioning", "beach",
      "pet friendly", "airport shuttle", "room service"
    ];
    document.querySelectorAll("li, [role='listitem'], button, span, div").forEach(el => {
      const t = clean(el.textContent);
      if (t.length > 2 && t.length < 90) {
        const low = t.toLowerCase();
        if (keywords.some(k => low === k || low.includes(k))) labels.add(t);
      }
    });
    return [...labels].slice(0, 40);
  }

  function extract() {
    const ld = findHotelLd();
    const body = allVisibleText();

    const name = firstNonEmpty([
      ld?.name,
      text("h1"),
      meta("og:title"),
      document.title.replace(/\s*\|.*$/, "")
    ]);

    const rating = firstNonEmpty([
      ld?.aggregateRating?.ratingValue,
      text('[aria-label*="out of 5"]'),
      text('[data-stid*="rating"]')
    ]);

    const reviews = firstNonEmpty([
      ld?.aggregateRating?.reviewCount,
      ld?.aggregateRating?.ratingCount
    ]);

    const address = ld?.address || {};
    const images = [
      ...(ld?.image ? (Array.isArray(ld.image) ? ld.image : [ld.image]) : []),
      ...[...document.images].map(i => i.currentSrc || i.src).filter(Boolean)
    ];

    const uniqueImages = [...new Set(images)]
      .filter(u => /^https?:/i.test(u))
      .slice(0, 80);

    const price = firstNonEmpty([
      ld?.priceRange,
      meta("price")
    ]);

    return {
      source: "Expedia",
      url: location.href,
      scraped_at: new Date().toISOString(),

      property: {
        name,
        type: firstNonEmpty([ld?.["@type"], ""]),
        address: clean([
          address.streetAddress,
          address.addressLocality,
          address.addressRegion,
          address.postalCode,
          address.addressCountry
        ].filter(Boolean).join(", ")),
        rating,
        review_count: reviews,
        price_range: price
      },

      stay: {
        visible_page_text_price_hint: firstNonEmpty([
          text('[data-stid*="price"]'),
          text('[class*="price"]')
        ]),
        visible_page_text: body.slice(0, 2500)
      },

      rooms: [],
      dining: [],
      facilities: {
        amenities: collectAmenities()
      },

      policies: {},

      images: uniqueImages,

      raw: {
        json_ld: ld || null
      }
    };
  }

  chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === "SCAN_HOTEL") {
      try {
        sendResponse({ok: true, data: extract()});
      } catch (e) {
        sendResponse({ok: false, error: String(e)});
      }
    }
    return true;
  });
})();