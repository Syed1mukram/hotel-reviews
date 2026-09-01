(() => {
  function clean(s) {
    return (s || "")
      .replace(/\\s*⬇\\s*Download\\s*/gi, " ")
      .replace(/\\s+/g, " ")
      .trim();
  }

  function first(re, text) {
    const m = text.match(re);
    return m ? clean(m[1] || m[0]) : "";
  }

  function unique(arr) {
    return [...new Set(arr.map(clean).filter(Boolean))];
  }

  function bodyText() {
    return clean(document.body?.innerText || "");
  }

  function parseRating(text) {
    const score = first(/(\d+(?:\.\d+)?)\s+out of 10/i, text);
    const reviews = first(/(\d[\d,]*)\s+reviews?/i, text);
    const label = first(
      /\d+(?:\.\d+)?\s+out of 10\s+([^0-9]{2,40}?)(?:See all|Highlights|About)/i,
      text
    );

    return {
      score: score ? Number(score) : null,
      out_of: score ? 10 : null,
      label: label || "",
      reviews: reviews ? Number(reviews.replace(/,/g, "")) : null
    };
  }

  function parseAddress(text) {
    const m = text.match(
      /Explore the area\s+View in a map\s+([^]+?)\s+View in a map\s+[A-Z][^]*?(?=See all about this area)/i
    );
    if (m) {
      const candidate = clean(m[1]);
      if (candidate.length > 10 && !/^(View in a map|Indira Gandhi)/i.test(candidate)) {
        return candidate;
      }
    }

    const fallback = text.match(
      /(\d+[-\w/]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*\d{5,6})/
    );
    return fallback ? clean(fallback[1]) : "";
  }

  function parseNearby(text) {
    const section = text.split("Explore the area")[1]?.split("See all about this area")[0] || "";
    const out = [];

    for (const m of section.matchAll(
      /([A-Z][A-Za-z0-9'’ .&()\-]{2,90}?)\s+(?:Place,\s*)?(?:‪)?(\d+)\s*(min|hr)\s*(walk|drive)/gi
    )) {
      const name = clean(m[1])
        .replace(/\s+Place$/i, "")
        .replace(/\s+Place,\s*$/i, "");

      if (name.length > 2 && !/View in a map|Explore the area/i.test(name)) {
        out.push({
          name,
          distance: `${m[2]} ${m[3]} ${m[4]}`
        });
      }
    }

    return unique(out.map(x => JSON.stringify(x)))
      .map(x => JSON.parse(x))
      .slice(0, 30);
  }

  function parseRooms(text) {
    const out = [];
    const marker = "View all photos for ";
    let start = 0;

    while (true) {
      const idx = text.indexOf(marker, start);
      if (idx < 0) break;

      const next = text.indexOf(marker, idx + marker.length);
      const block = text.slice(idx + marker.length, next < 0 ? idx + 3500 : next);

      const roomLine = block.match(
        /^(.+?)\s+\|\s+(.+?)(?=\s+\d+\s+sq\s*ft|\s+\d+\s+bedroom|\s+Sleeps)/i
      );

      let name = roomLine
        ? clean(roomLine[1])
        : clean(block.split(/\s+/).slice(0, 4).join(" "));

      // Expedia repeats the room name after the pipe. Keep one clean name.
      const repeated = name.match(/^(.+?)\s+\1$/i);
      if (repeated) name = clean(repeated[1]);

      const detailsMatch = block.match(
        /^.+?\|\s*(.+?)(?=\s+\d+\s+(?:sq\s*ft|bedroom)|\s+Sleeps)/i
      );

      const size = first(/(\d[\d,]*)\s*sq\s*ft/i, block);
      const sleeps = first(/Sleeps\s+(\d+)/i, block);
      const bedrooms = first(/(\d+)\s+bedroom/i, block);

      const bed = first(
        /(?:Sleeps\s+\d+[\s\S]{0,100}?)(\d+\s+(?:Queen|King|Twin|Double|Single)\s+Bed(?:\s+OR\s+\d+\s+(?:Queen|King|Twin|Double|Single)\s+Bed)?)/i,
        block
      );

      const nightly = first(/\$(\d+(?:\.\d+)?)\s+nightly/i, block);
      const total = first(/\$(\d+(?:\.\d+)?)\s+total/i, block);

      const previous = first(
        /(?:The\s+)?previous price was\s+\$?([\d,.]+)/i,
        block
      );

      const breakfast = first(
        /Breakfast\s*\+\s*\$?([\d,.]+)/i,
        block
      );

      const refundable = block.match(
        /Fully refundable(?:\s+Before\s+(?:Thu|Fri|Sat|Sun|Mon|Tue|Wed),\s+[A-Z][a-z]{2}\s+\d{1,2})?/i
      );

      const amenities = unique([
        /WiFi\s*\(free\)/i.test(block) ? "Free WiFi" : "",
        /In-room safe/i.test(block) ? "In-room safe" : "",
        /\bdesk\b/i.test(block) ? "Desk" : ""
      ]);

      if (size || sleeps || nightly || total || bed) {
        out.push({
          name,
          room_details: detailsMatch ? clean(detailsMatch[1]) : "",
          size_sq_ft: size ? Number(size.replace(/,/g, "")) : null,
          bedrooms: bedrooms ? Number(bedrooms) : null,
          sleeps: sleeps ? Number(sleeps) : null,
          bed,
          amenities,
          nightly_price: nightly ? Number(nightly.replace(/,/g, "")) : null,
          total_price: total ? Number(total.replace(/,/g, "")) : null,
          previous_price: previous ? Number(previous.replace(/,/g, "")) : null,
          breakfast_extra: breakfast ? Number(breakfast.replace(/,/g, "")) : null,
          cancellation: refundable ? clean(refundable[0]) : ""
        });
      }

      start = idx + marker.length;
    }

    return out;
  }

  function parsePolicies(text) {
    const section = text.split("Policies")[1]?.split("Reviews")[0] || text;
    return {
      check_in: first(/Check-in start time:\s*([^;]+)/i, section),
      check_in_end: first(/Check-in end time:\s*([^;]+)/i, section),
      minimum_check_in_age: first(/Minimum check-in age:\s*(\d+)/i, section),
      check_out: first(/Check-out before\s+([^\.\n]+?)(?=\s+Special check-in instructions|$)/i, section),
      pets: /Pets\s+Pets not allowed/i.test(section) ? "Pets not allowed" : "",
      children: /Children and extra beds\s+Children are welcome/i.test(section) ? "Children are welcome" : "",
      rollaway_extra_bed: first(/Rollaway\/extra beds are available for\s+([^\.\n]+?)(?=\s+Cribs|$)/i, section),
      cribs: first(/Cribs \(infant beds\) are\s+([^\.\n]+?)(?=\s+Property payment types|$)/i, section),
      payment: /This property accepts credit cards/i.test(section) ? "Credit cards accepted" : "",
      cancellation: first(/Fully refundable(?:\s+Reserve now, pay later)?/i, text)
    };
  }

  function collectAmenities(text) {
    const candidates = [
      "Free WiFi", "WiFi", "Air conditioning", "Housekeeping",
      "Room service", "Extra beds", "Business facilities", "Parking",
      "Breakfast", "Restaurant", "Bar", "Pool", "Spa", "Gym",
      "Fitness", "Beach", "Kids club", "Airport shuttle"
    ];

    return candidates.filter(x =>
      new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i").test(text)
    );
  }

  function parseReviews(text) {
    const categoryScores = {};

    const categoryMap = {
      cleanliness: /(\d+(?:\.\d+)?)\s+Cleanliness\s+Cleanliness,\s*\1\s+out of 10/i,
      location: /(\d+(?:\.\d+)?)\s+Location\s+Location,\s*\1\s+out of 10/i,
      service: /(\d+(?:\.\d+)?)\s+Service\s+Service,\s*\1\s+out of 10/i,
      comfort: /(\d+(?:\.\d+)?)\s+Comfort\s+Comfort,\s*\1\s+out of 10/i,
      value: /(\d+(?:\.\d+)?)\s+Value\s+Value,\s*\1\s+out of 10/i
    };

    for (const [key, re] of Object.entries(categoryMap)) {
      const m = text.match(re);
      if (m) categoryScores[key] = Number(m[1]);
    }

    const reviewSection = text.split("Guest reviews")[1]?.split("See all 17 reviews")[0] || "";
    const snippets = [];

    for (const m of reviewSection.matchAll(
      /(\d+\/10)\s+([A-Za-z]+)\s+.*?(?:See more\s+)?(?:from\s+)?([^,]{2,50})'s,\s*([A-Z][a-z]{2}\s+\d{1,2},\s+\d{4})\s+review/gi
    )) {
      snippets.push({
        score: m[1],
        label: clean(m[2]),
        reviewer: clean(m[3]),
        date: clean(m[4])
      });
    }

    return {
      category_scores: categoryScores,
      verified_reviews: Number(first(/(\d[\d,]*)\s+verified reviews/i, text) || 0),
      highlights: snippets.slice(0, 20)
    };
  }


  function parseReviewCategories(text) {
    const categories = [];
    const patterns = [
      ["cleanliness", /(\d+(?:\.\d+)?)\s+Cleanliness\s+Cleanliness/i],
      ["location", /(\d+(?:\.\d+)?)\s+Location\s+Location/i],
      ["service", /(\d+(?:\.\d+)?)\s+Service\s+Service/i],
      ["comfort", /(\d+(?:\.\d+)?)\s+Comfort\s+Comfort/i],
      ["facilities", /(\d+(?:\.\d+)?)\s+Facilities\s+Facilities/i],
      ["staff", /(\d+(?:\.\d+)?)\s+Staff\s+Staff/i],
      ["value", /(\d+(?:\.\d+)?)\s+Value\s+Value/i]
    ];

    for (const [name, re] of patterns) {
      const score = first(re, text);
      if (score) categories.push({
        category: name,
        score: Number(score),
        out_of: 10
      });
    }

    return categories;
  }

  function parseGuestReviews(text) {
    const section =
      text.split("Guest reviews")[1]?.split("See all 17 reviews")[0]
      || text.split("Guest reviews")[1]?.slice(0, 9000)
      || "";

    const reviews = [];

    // Expedia repeats the score/sentiment twice:
    // "10/10 Excellent 10 out of 10 Excellent comment See more ..."
    // Capture the actual comment only after the second score/sentiment pair.
    const re =
      /(\d+)\/10\s+(Excellent|Very good|Good|Average|Poor|Terrible)\s+\1\s+out of 10\s+\2\s+(.+?)(?=\s+See more\s+See more from|\s+\d+\/10\s+(?:Excellent|Very good|Good|Average|Poor|Terrible)|\s+See all \d+ reviews|$)/gis;

    for (const m of section.matchAll(re)) {
      const score = Number(m[1]);
      const sentiment = clean(m[2]);
      const comment = clean(m[3]);

      if (comment && comment.length > 1) {
        reviews.push({
          score,
          out_of: 10,
          sentiment,
          comment: comment.slice(0, 800)
        });
      }
    }

    // Fallback for pages where Expedia does not repeat "out of 10".
    if (!reviews.length) {
      const fallback =
        /(\d+)\/10\s+(Excellent|Very good|Good|Average|Poor|Terrible)\s+(.+?)(?=\s+See more\s+See more from|\s+\d+\/10\s+(?:Excellent|Very good|Good|Average|Poor|Terrible)|\s+See all \d+ reviews|$)/gis;

      for (const m of section.matchAll(fallback)) {
        const score = Number(m[1]);
        const sentiment = clean(m[2]);
        const comment = clean(m[3]);

        if (comment && !/^\d+\s+out of$/i.test(comment)) {
          reviews.push({
            score,
            out_of: 10,
            sentiment,
            comment: comment.slice(0, 800)
          });
        }
      }
    }

    return reviews.slice(0, 30);
  }

  function parseHighlights(text) {
    const section = text.split("Highlights for your")[1]?.split("About this property")[0] || "";
    const out = [];
    const couple = section.match(/Highly rated by couples\s+(.+?)(?=\s+Discover nearby landmarks|$)/i);
    const walk = section.match(/Walk to\s+(.+?)(?=\s+About this property|$)/i);
    if (couple) out.push("Highly rated by couples: " + clean(couple[1]));
    if (walk) out.push("Walk to " + clean(walk[1]));
    return unique(out).filter(x => x.length > 8 && x.length < 250);
  }

  function parseAccessibility(text) {
    const section = text.split("Accessibility")[1]?.split("Policies")[0] || "";
    return {
      elevator: /Elevator/i.test(section),
      common_areas: /Common areas/i.test(section),
      accessibility_text: clean(section).slice(0, 1000)
    };
  }

  function parsePayment(text) {
    const section = text.split("Property payment types")[1]?.split("Important information")[0] || "";
    return unique(
      section.split(/\s{2,}|(?=Credit cards|cash|debit|PayPal)/i)
        .map(clean)
        .filter(x => x.length > 2 && x.length < 150)
    ).slice(0, 15);
  }

  function parseHotelSections(text) {
    return {
      pool: /Pool/i.test(text),
      spa: /Spa/i.test(text),
      gym: /Gym|Fitness/i.test(text),
      beach: /Beach/i.test(text),
      restaurant: /Restaurant/i.test(text),
      bar: /Bar/i.test(text),
      kids: /Kids|Children/i.test(text),
      parking: /Parking/i.test(text),
      wifi: /WiFi/i.test(text)
    };
  }

  function scanHotel() {
    const text = bodyText();

    const name =
      first(/Photo gallery for\s+(.+?)\s+Reception/i, text) ||
      clean(document.querySelector("h1")?.textContent) ||
      clean(document.title.replace(/\s*\|.*$/, ""));

    const start = first(/Start date\s+([A-Z][a-z]{2}\s+\d{1,2})/i, text);
    const end = first(/End date\s+([A-Z][a-z]{2}\s+\d{1,2})/i, text);

    const travelerBlock = first(
      /Travelers\s+(\d+\s+travelers?,\s*\d+\s+room)/i,
      text
    );

    const adultsMatch = travelerBlock.match(/(\d+)\s+travelers?/i);
    const roomsMatch = travelerBlock.match(/(\d+)\s+room/i);

    const nightly = first(/\$(\d+(?:\.\d+)?)\s+nightly/i, text);
    const total = first(/\$(\d+(?:\.\d+)?)\s+total/i, text);
    const previous = first(/previous price was\s+\$?([\d,.]+)/i, text);
    const discount = first(/(\$\d+\s+off)/i, text);

    const images = unique(
      [...document.images]
        .map(i => i.currentSrc || i.src)
        .filter(u => /^https?:/i.test(u))
        .filter(u => /images\.trvl-media\.com\/lodging/i.test(u))
    ).slice(0, 100);

    return {
      source: "Expedia",
      url: location.href,
      scraped_at: new Date().toISOString(),

      property: {
        name,
        type: /Property class:\s*\d+/i.test(text) ? "Hotel" : "",
        property_class: first(/Property class:\s*(\d+)/i, text),
        address: parseAddress(text),
        rating: parseRating(text)
      },

      stay: {
        check_in: start,
        check_out: end,
        adults: adultsMatch ? Number(adultsMatch[1]) : null,
        rooms: roomsMatch ? Number(roomsMatch[1]) : null,
        traveler_text: travelerBlock
      },

      price: {
        nightly: nightly ? Number(nightly.replace(/,/g, "")) : null,
        total: total ? Number(total.replace(/,/g, "")) : null,
        previous: previous ? Number(previous.replace(/,/g, "")) : null,
        discount,
        currency: "USD"
      },

      rooms: parseRooms(text),

      dining: {
        breakfast_available: /Breakfast/i.test(text),
        restaurants: /Restaurant/i.test(text),
        bars: /Bar/i.test(text)
      },

      facilities: {
        amenities: collectAmenities(text)
      },

      location: {
        address: parseAddress(text),
        nearby: parseNearby(text)
      },

      policies: {
        cancellation: first(/(Fully refundable[^.]{0,120})/i, text),
        payment: first(/(Reserve now, pay later[^.]{0,100})/i, text),
        check_in: first(/Check-in start time:\s*([^;]+)/i, text),
        check_in_end: first(/Check-in end time:\s*([^;]+)/i, text),
        minimum_check_in_age: first(/Minimum check-in age:\s*(\d+)/i, text),
        check_out: first(/Check-out before\s+([^\.\n]+)/i, text),
        pets: /Pets not allowed/i.test(text) ? "Pets not allowed" : "",
        children: /Children are welcome/i.test(text) ? "Children are welcome" : "",
        rollaway_extra_bed: first(/Rollaway\/extra beds are available for\s+([^\.\n]+)/i, text),
        cribs: first(/Cribs \(infant beds\) are ([^.\n]+)/i, text)
      },

      reviews: {
        categories: parseReviewCategories(text),
        guest_reviews: parseGuestReviews(text)
      },

      highlights: parseHighlights(text),

      accessibility: parseAccessibility(text),

      payment_types: parsePayment(text),

      hotel_sections: parseHotelSections(text),

      images,

      raw: {
        visible_page_text: text.slice(0, 12000)
      }
    };
  }

  window.__expediaScanHotel = scanHotel;
})();