(() => {
  function clean(s) {
    return (s || "")
      .replace(/\s*⬇\s*Download\s*/gi, " ")
      .replace(/\s*Download\s*/gi, " ")
      .replace(/\s+/g, " ")
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
    const patterns=[
      /(\d{1,5}[-\w/]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*\d{5,6})/,
      /(\d{1,5}[-\w/]+,\s*[^,]+,\s*[^,]+,\s*[^,]+,\s*\d{5,6})/
    ];
    for(const re of patterns){const m=text.match(re);if(m)return clean(m[1]);}
    const m=text.match(/View in a map\s+(\d{1,5}[-\w/]+,\s*.+?\d{5,6})\s+View in a map/i);
    return m?clean(m[1]):"";
  }

function parseNearby(text) {
    const out=[];
    const re=/([A-Z][A-Za-z0-9'’ .&()\-]{2,100}?)\s+(?:Place,?\s*)?(?:‪)?(\d+)\s*(min|hr)\s*(walk|drive)/gi;
    for(const m of text.matchAll(re)){
      let name=clean(m[1]).replace(/\s+Place[,]?$/i,"");
      if(name && !/^(Explore the area|View in a map)$/i.test(name) && !/^\d/.test(name))
        out.push({name,distance:`${m[2]} ${m[3]} ${m[4]}`});
    }
    const seen=new Set();
    return out.filter(x=>{const k=x.name+"|"+x.distance;if(seen.has(k))return false;seen.add(k);return true}).slice(0,30);
  }

function parseRooms(baseText) {
    const out = [];
    const marker = "View all photos for ";
    let start = 0;

    while (true) {
      const idx = baseText.indexOf(marker, start);
      if (idx < 0) break;

      const next = baseText.indexOf(marker, idx + marker.length);
      const block = baseText.slice(idx + marker.length, next < 0 ? idx + 3500 : next);

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
    const section = (text.split(/\bPolicies\b/i)[1] || text)
      .split(/\bReviews\b/i)[0]
      .split(/\bSee all reviews\b/i)[0];

    const capture = (re) => {
      const m = section.match(re);
      return m ? clean(m[1]) : "";
    };

    return {
      cancellation: /Fully refundable/i.test(section) ? "Fully refundable" : "",
      check_in: capture(/Check-in start time:\s*([0-9:]+\s*(?:AM|PM))/i),
      check_in_end: capture(/Check-in end time:\s*([^\n;]+?)(?=\s*Minimum check-in age:)/i),
      minimum_check_in_age: capture(/Minimum check-in age:\s*(\d+)/i),
      check_out: capture(/Check-out before\s*([0-9:]+\s*(?:AM|PM))/i),
      pets: /Pets\s+Pets not allowed/i.test(section) ? "Pets not allowed" : "",
      children: /Children and extra beds\s+Children are welcome/i.test(section) ? "Children are welcome" : "",
      rollaway_extra_bed: capture(/Rollaway\/extra beds are available for\s*([A-Z]{2,4}\s*[\d,.]+\s*per night)/i),
      cribs: capture(/Cribs \(infant beds\) are\s*(not available|available)/i),
      payment: /This property accepts credit cards/i.test(section) ? "Credit cards accepted" : ""
    };
  }

  function collectAmenities(baseText) {
    const candidates = [
      "Free WiFi", "WiFi", "Air conditioning", "Housekeeping",
      "Room service", "Extra beds", "Business facilities", "Parking",
      "Breakfast", "Restaurant", "Pool", "Spa", "Gym",
      "Fitness", "Beach", "Kids club", "Airport shuttle"
    ];

    return candidates.filter(x =>
      new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i").test(baseText)
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
    const categories=[];
    const labels=["Cleanliness","Location","Service","Comfort","Facilities","Staff","Value"];
    for(const label of labels){
      const re=new RegExp("(?:^|\\s)(\\d+(?:\\.\\d+)?)\\s+"+label+"(?:\\s+"+label+")?(?=\\s|$)","i");
      const m=text.match(re);
      if(m) categories.push({category:label.toLowerCase(),score:Number(m[1]),out_of:10});
    }
    return categories;
  }

  function parseGuestReviews(text) {
    const raw=String(text||"").replace(/\r/g,"");
    const lines=raw.split(/\n+/).map(x=>clean(x)).filter(Boolean);
    const out=[];
    const scoreRe=/^(\d+(?:\.\d+)?)\s*(?:\/10|out of 10)\s+(Excellent|Very good|Good|Average|Poor|Terrible)$/i;

    for(let i=0;i<lines.length;i++){
      const sm=lines[i].match(scoreRe);
      if(!sm) continue;

      const score=Number(sm[1]);
      const sentiment=clean(sm[2]);
      let reviewer="";
      let date="";
      let comment="";
      let liked="";

      // Typical card:
      // score/sentiment
      // reviewer
      // date
      // Liked: ...
      // comment
      // Stayed 1 night...
      let j=i+1;

      if(j<lines.length && !/^(?:Verified review|Verified traveler|Liked:|Stayed|More reviews|Image \d+)/i.test(lines[j])){
        reviewer=lines[j++];
      }
      if(j<lines.length && /^[A-Z][A-Za-z]{2,10}\s+\d{1,2},\s+\d{4}$/.test(lines[j])){
        date=lines[j++];
      }
      if(j<lines.length && /^Liked:/i.test(lines[j])){
        liked=lines[j++];
      } else if(j<lines.length && /^Verified traveler/i.test(lines[j])){
        // Some cards put "Verified traveler" before the date.
        reviewer=reviewer || lines[j++];
        if(j<lines.length && /^[A-Z][A-Za-z]{2,10}\s+\d{1,2},\s+\d{4}$/.test(lines[j])) date=lines[j++];
        if(j<lines.length && /^Liked:/i.test(lines[j])) liked=lines[j++];
      }

      const parts=[];
      while(j<lines.length){
        if(scoreRe.test(lines[j])) break;
        if(/^See all \d+\s+reviews/i.test(lines[j])) break;
        if(/^More reviews$/i.test(lines[j])) break;
        if(/^Image \d+\s+out of\s+\d+/i.test(lines[j])) break;
        if(/^Chat Window|^Your Privacy Choices|^© \d{4} Expedia/i.test(lines[j])) break;
        if(/^Stayed \d+\s+night/i.test(lines[j])) break;
        if(/^Verified review$/i.test(lines[j])) { j++; continue; }

        // If Expedia puts reviewer/date metadata on one line, don't turn it
        // into the review comment.
        if(/^(?:Verified traveler|Traveled with partner|Traveled with family|Traveled with friends|Business traveler)/i.test(lines[j])){
          j++; continue;
        }

        parts.push(lines[j]);
        j++;
      }

      comment=clean(parts.join(" "));
      comment=comment.replace(/^More reviews.*$/i,"").trim();

      if(comment && comment.length>1200) comment=comment.slice(0,1200);
      if(comment){
        out.push({
          comment,
          out_of:10,
          score,
          sentiment
        });
      }
    }

    // Fallback for Expedia layouts where line breaks are collapsed.
    if(!out.length){
      const flat=clean(raw);
      const re=new RegExp(
        "(\\d+(?:\\.\\d+)?)\\s*\\/10\\s+(Excellent|Very good|Good|Average|Poor|Terrible)\\s+"+
        "(.{3,500}?)(?=\\s+\\d+(?:\\.\\d+)?\\/10\\s+|\\s+See all\\s+\\d+\\s+reviews|$)",
        "gi"
      );
      for(const m of flat.matchAll(re)){
        let c=clean(m[3]);
        c=c.replace(/(?:Stayed \d+ night.*)$/i,"").trim();
        if(c.length>2) out.push({comment:c.slice(0,1200),out_of:10,score:Number(m[1]),sentiment:clean(m[2])});
      }
    }

    const seen=new Set();
    return out.filter(r=>{
      const k=r.score+"|"+r.comment;
      if(seen.has(k)) return false;
      seen.add(k);
      return true;
    }).slice(0,30);
  }
  function parseRoomAmenityDetails(text) {
    const t=clean(text||"");
    const groups={};
    const add=(group,items)=>{ const vals=unique(items||[]); if(vals.length) groups[group]=vals; };
    const find=(re)=>{ const m=t.match(re); return m?m[1]:""; };

    add("bathroom", [
      /Free toiletries/i.test(t)?"Free toiletries":"",
      /Private bathroom/i.test(t)?"Private bathroom":"",
      /Shampoo/i.test(t)?"Shampoo":"",
      /Shower/i.test(t)?"Shower":"",
      /Soap/i.test(t)?"Soap":"",
      /Toilet paper/i.test(t)?"Toilet paper":"",
      /Towels provided/i.test(t)?"Towels provided":""
    ]);
    add("food_and_drink", [
      /Coffee\/tea maker/i.test(t)?"Coffee/tea maker":"",
      /Electric kettle/i.test(t)?"Electric kettle":"",
      /Free bottled water/i.test(t)?"Free bottled water":"",
      /Limited room service/i.test(t)?"Limited room service":"",
      /Mini-fridge/i.test(t)?"Mini-fridge":""
    ]);
    add("entertainment", [/Flat-screen TV with cable channels/i.test(t)?"Flat-screen TV with cable channels":""]);
    add("room_features", [
      /Air conditioning \(climate-controlled\)/i.test(t)?"Air conditioning (climate-controlled)":"",
      /Ceiling fan/i.test(t)?"Ceiling fan":"",
      /Desk/i.test(t)?"Desk":"",
      /Free daily newspapers/i.test(t)?"Free daily newspapers":"",
      /Safe/i.test(t)?"Safe":""
    ]);
    return groups;
  }

  function parseDiningDetails(text) {
    const section = text.split("About this property")[1]?.split("Explore the area")[0] || "";
    const out = {
      restaurants: [],
      breakfast: "",
      dining_notes: []
    };

    if (/restaurant/i.test(section)) out.restaurants.push("Restaurant available");
    const breakfast = section.match(/Breakfast(?: meal| included| for a fee)?/i);
    if (breakfast) out.breakfast = clean(breakfast[0]);

    return out;
  }

  function parseActivities(text) {
    const lower = text.toLowerCase();
    const keywords = [
      ["pool", "Pool"],
      ["spa", "Spa"],
      ["gym", "Gym"],
      ["fitness", "Fitness"],
      ["kids", "Kids/family facilities"],
      ["children", "Children/family facilities"],
      ["beach", "Beach"],
      ["water sports", "Water sports"],
      ["tennis", "Tennis"],
      ["golf", "Golf"],
      ["sauna", "Sauna"],
      ["steam room", "Steam room"],
      ["massage", "Massage"],
      ["bicycle", "Bicycle"],
      ["hiking", "Hiking"]
    ];
    return keywords.filter(([k]) => lower.includes(k)).map(([,v]) => v);
  }

  function parseReviewSummary(text) {
    const out = {
      overall: "",
      cleanliness: "",
      location: "",
      service: "",
      comfort: "",
      value: "",
      guest_count: ""
    };

    const overall = text.match(/Reviews\s+(\d+(?:\.\d+)?)\s+(?:out of 10|\/10)/i);
    const count = text.match(/(\d+)\s+(?:verified\s+)?reviews/i);
    if (overall) out.overall = overall[1];
    if (count) out.guest_count = count[1];

    const cats = [
      ["cleanliness", /(\d+(?:\.\d+)?)\s+Cleanliness/i],
      ["location", /(\d+(?:\.\d+)?)\s+Location/i],
      ["service", /(\d+(?:\.\d+)?)\s+Service/i],
      ["comfort", /(\d+(?:\.\d+)?)\s+Comfort/i],
      ["value", /(\d+(?:\.\d+)?)\s+Value/i]
    ];
    for (const [key,re] of cats) {
      const m=text.match(re);
      if (m) out[key]=m[1];
    }
    return out;
  }

  function parseUsefulHighlights(text) {
    const out=[];
    const patterns=[
      /Highly rated by couples[^.]*\./i,
      /Walk to [^.]+/i,
      /Price is lower than usual[^.]*\./i,
      /Our lowest price/i
    ];
    for (const re of patterns) {
      const m=text.match(re);
      if (m) out.push(clean(m[0]));
    }
    return unique(out);
  }


  function parseAmenityGroups(text) {
    const groups = {
      internet: [],
      parking: [],
      family: [],
      conveniences: [],
      guest_services: [],
      business_services: [],
      accessibility: [],
      other: []
    };

    const add = (group, value) => {
      value = clean(value);
      if (value && !groups[group].includes(value)) groups[group].push(value);
    };

    const has = (re) => re.test(text);

    if (has(/Available in all rooms:\s*Free WiFi/i)) add("internet", "Free WiFi in all rooms");
    if (has(/Available in some public areas:\s*Free WiFi/i)) add("internet", "Free WiFi in public areas");
    if (!groups.internet.length && has(/\bFree WiFi\b/i)) add("internet", "Free WiFi");

    if (has(/No onsite parking available/i)) add("parking", "No onsite parking available");
    else if (has(/\bParking\b/i)) add("parking", "Parking available");

    if (has(/No pets allowed/i)) add("other", "Pets not allowed");

    const family = [
      "Laundry facilities", "Mini-fridge", "Kids' meals",
      "Cribs/infant beds", "Rollaway/extra beds"
    ];
    for (const x of family) {
      if (has(new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))) {
        add("family", x);
      }
    }

    const convenience = [
      "24-hour front desk", "Lockers", "Luggage storage",
      "Newspapers in lobby", "Laundry facilities"
    ];
    for (const x of convenience) {
      if (has(new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))) {
        add("conveniences", x);
      }
    }

    const guest = ["Housekeeping (daily)", "Multilingual staff", "Room service"];
    for (const x of guest) {
      if (has(new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))) {
        add("guest_services", x);
      }
    }

    const business = ["Business center", "Meeting room", "Business facilities"];
    for (const x of business) {
      if (has(new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))) {
        add("business_services", x);
      }
    }

    if (has(/\bElevator\b/i)) add("accessibility", "Elevator");
    if (has(/\bCommon areas\b/i)) add("accessibility", "Common areas");

    const other = ["Banquet hall"];
    for (const x of other) {
      if (has(new RegExp(x.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "i"))) {
        add("other", x);
      }
    }

    return groups;
  }


  async function openAllPropertyAmenities() {
    const candidates = [...document.querySelectorAll("button, a, [role='button']")];
    const target = candidates.find(el =>
      /see all about this property/i.test(clean(el.innerText || el.textContent || ""))
    );

    if (!target) return false;

    try {
      target.scrollIntoView({block: "center", behavior: "instant"});
      target.click();
      await new Promise(resolve => setTimeout(resolve, 1000));
      return true;
    } catch {
      return false;
    }
  }

  function expandedAmenityText() {
    const dialogs = [...document.querySelectorAll('[role="dialog"], [aria-modal="true"]')];
    if (!dialogs.length) return "";
    const dialog = dialogs[dialogs.length - 1];
    return clean(dialog.innerText || dialog.textContent || "");
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
      kids: /Kids|Children/i.test(text),
      parking: /Parking/i.test(text),
      wifi: /WiFi/i.test(text)
    };
  }

  function parsePoliciesClean(text) {
    // Expedia can show Policies directly on the page, inside a "See all policies"
    // dialog, or later in the document after other sections. Do NOT split on the
    // first occurrence of "Policies" because Expedia also has footer/privacy
    // policy text. Parse the policy phrases directly from the complete text.
    const section = clean(text || "");
    const get = (re) => {
      const m = section.match(re);
      return m ? clean(m[1]) : "";
    };

    const out = {
      cancellation: /Fully refundable/i.test(section) ? "Fully refundable" : "",
      payment: /This property accepts credit cards/i.test(section) ? "Credit cards accepted" : "",
      check_in: get(/Check-in start time:\s*([0-9:]+\s*(?:AM|PM))/i) ||
                get(/Check-in\s*([0-9:]+\s*(?:AM|PM))\s*[-–—]?\s*Check-in end/i),
      check_in_end: get(/Check-in end time:\s*([^;\n]+?)(?=\s*Minimum check-in age:|\s*Check-out)/i),
      minimum_check_in_age: get(/Minimum check-in age:\s*(\d+)/i),
      check_out: get(/Check-out before\s*([0-9:]+\s*(?:AM|PM))/i),
      pets: /Pets\s+Pets not allowed/i.test(section) ? "Pets not allowed" :
            (/Pets not allowed/i.test(section) ? "Pets not allowed" : ""),
      children: /Children and extra beds\s+Children are welcome/i.test(section) ? "Children are welcome" :
                (/Children are welcome/i.test(section) ? "Children are welcome" : ""),
      rollaway_extra_bed: get(/Rollaway\/extra beds are available for\s*([A-Z]{2,4}\s*[\d,.]+\s*per night)/i),
      cribs: get(/Cribs\s*\(infant beds\)\s*are\s*(not available|available)/i),
      check_in_instructions: get(/Special check-in instructions\s*([\s\S]*?)(?=\s*Access methods|\s*Pets\s+Pets|\s*Children and extra beds|\s*Property payment types)/i),
      access_method: get(/Access methods\s*([\s\S]*?)(?=\s*Pets\s+Pets|\s*Children and extra beds|\s*Property payment types)/i),
      identification: get(/Government-issued photo identification and a credit card, debit card or cash deposit may be required at check-in[^.]*\.?/i),
      special_requests: get(/Special requests are subject to availability at check-in[^.]*\.?/i),
      important_information: get(/You need to know\s*([\s\S]*?)(?=\s*This property accepts|\s*Safety features|\s*We should mention|$)/i)
    };

    return out;
  }

  async function captureExpediaText(targetRe, options={}) {
    const candidates=[...document.querySelectorAll("button,a,[role='button'],[role='tab']")];
    const target=candidates.find(el=>targetRe.test(clean(el.innerText||el.textContent||el.getAttribute("aria-label")||"")));
    if(!target) return "";
    try{
      target.scrollIntoView({block:"center",behavior:"instant"});
      target.click();
      for(let attempt=0;attempt<20;attempt++){
        await new Promise(r=>setTimeout(r,500));
        if(/pwaDialog=summary-reviews/i.test(location.href)){
          window.scrollTo(0,document.documentElement.scrollHeight);
          await new Promise(r=>setTimeout(r,500));
          window.scrollTo(0,0);
          await new Promise(r=>setTimeout(r,500));
          const body=clean(document.body?.innerText||"");
          if(/\b\d+(?:\.\d+)?\s*(?:\/10|out of 10)\b/i.test(body) &&
             /See all\s+\d+\s+reviews|Verified review|See more from/i.test(body)) return body;
        }
        const ds=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')];
        if(ds.length){
          const dialog=ds[ds.length-1], t=clean(dialog.innerText||"");
          if(/\b\d+(?:\.\d+)?\s*(?:\/10|out of 10)\b/i.test(t) ||
             /Verified review|See more from|Guest reviews/i.test(t)){
            const scroller=[...dialog.querySelectorAll("*")].find(el=>{
              const st=getComputedStyle(el);
              return (st.overflowY==="auto"||st.overflowY==="scroll") && el.scrollHeight>el.clientHeight+100;
            }) || dialog;
            for(let k=0;k<6;k++){ scroller.scrollTop=scroller.scrollHeight; await new Promise(r=>setTimeout(r,300)); }
            scroller.scrollTop=0;
            await new Promise(r=>setTimeout(r,300));
            return dialog.innerText||dialog.textContent||"";
          }
        }
      }
      return document.body?.innerText||"";
    }catch{return document.body?.innerText||"";}
  }
  function closeExpediaDialog(){
    const dialogs=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')];
    if(!dialogs.length)return;
    const d=dialogs[dialogs.length-1];
    const btn=[...d.querySelectorAll("button,[role='button']")].find(b=>/close|^×$/i.test(clean(b.getAttribute("aria-label")||b.innerText||"")));
    try{(btn||d.querySelector("button"))?.click()}catch{}
  }

  async function capturePoliciesTab(){
    const candidates=[...document.querySelectorAll("button,a,[role='tab']")];
    const target=candidates.find(el=>/^Policies$/i.test(clean(el.innerText||el.textContent||"")));
    if(!target)return "";
    try{
      target.click();
      await new Promise(r=>setTimeout(r,500));
      return document.body?.innerText||"";
    }catch{return ""}
  }

  async function captureLocationTab(){
    const candidates=[...document.querySelectorAll("button,a,[role='tab']")];
    const target=candidates.find(el=>/^Location$/i.test(clean(el.innerText||el.textContent||"")));
    if(!target)return "";
    try{
      target.click();
      await new Promise(r=>setTimeout(r,500));
      return document.body?.innerText||"";
    }catch{return ""}
  }

  async function captureExpandableSection(labelRe) {
    const candidates=[...document.querySelectorAll("button,a,[role='button'],[role='tab']")];
    const target=candidates.find(el=>labelRe.test(clean(el.innerText||el.textContent||el.getAttribute("aria-label")||"")));
    if(!target) return "";
    try{
      target.scrollIntoView({block:"center",behavior:"instant"});
      target.click();
      await new Promise(r=>setTimeout(r,700));

      const dialogs=[...document.querySelectorAll('[role="dialog"],[aria-modal="true"]')];
      if(dialogs.length){
        const d=dialogs[dialogs.length-1];
        const scroller=[...d.querySelectorAll("*")].find(el=>{
          const st=getComputedStyle(el);
          return (st.overflowY==="auto"||st.overflowY==="scroll") && el.scrollHeight>el.clientHeight+100;
        })||d;
        for(let k=0;k<8;k++){ scroller.scrollTop=scroller.scrollHeight; await new Promise(r=>setTimeout(r,250)); }
        const t=d.innerText||d.textContent||"";
        closeExpediaDialog();
        return t;
      }

      // Inline "See all / See more" sections expand in place.
      const t=document.body?.innerText||"";
      return t;
    }catch{return "";}
  }

  async function captureAllExpandableDetails() {
    const parts=[];

    // Property amenities -> modal
    await openAllPropertyAmenities();
    const prop=expandedAmenityText();
    if(prop) parts.push(prop);
    closeExpediaDialog();

    // Rooms -> room amenities / room details
    const roomTab=[...document.querySelectorAll("button,a,[role='tab']")]
      .find(el=>/^Rooms$/i.test(clean(el.innerText||el.textContent||"")));
    try{roomTab?.click(); await new Promise(r=>setTimeout(r,600));}catch{}
    for(const re of [
      /^(?:See all|See more).*room amenities$/i,
      /^See all room options$/i,
      /^See all$/i
    ]){
      const t=await captureExpandableSection(re);
      if(t) parts.push(t);
    }

    // Policies tab + its "See all policies" expander
    const polTab=[...document.querySelectorAll("button,a,[role='tab']")]
      .find(el=>/^Policies$/i.test(clean(el.innerText||el.textContent||"")));
    try{polTab?.click(); await new Promise(r=>setTimeout(r,600));}catch{}
    const pol=await captureExpandableSection(/^See all policies$/i);
    if(pol) parts.push(pol);
    const polBody=document.body?.innerText||"";
    if(polBody) parts.push(polBody);

    // Location tab + "See all about this area"
    const locTab=[...document.querySelectorAll("button,a,[role='tab']")]
      .find(el=>/^Location$/i.test(clean(el.innerText||el.textContent||"")));
    try{locTab?.click(); await new Promise(r=>setTimeout(r,600));}catch{}
    const area=await captureExpandableSection(/^See all about this area$/i);
    if(area) parts.push(area);
    const locBody=document.body?.innerText||"";
    if(locBody) parts.push(locBody);

    const overview=[...document.querySelectorAll("button,a,[role='tab']")]
      .find(el=>/^Overview$/i.test(clean(el.innerText||el.textContent||"")));
    try{overview?.click();}catch{}
    return parts.join(" ");
  }

  async function scanHotel() {
    const baseText=clean(bodyText());

    // Expedia hides a large part of the hotel data behind "See all / See more"
    // controls. Expand/capture those sections before parsing.
    const expandedText=await captureAllExpandableDetails();

    await openAllPropertyAmenities();
    const modalText=expandedAmenityText();
    closeExpediaDialog();

    // Capture the tabs/overlays Expedia uses for information that is not
    // present in the initial DOM text.
    const locationText=await captureLocationTab();
    const policiesText=await capturePoliciesTab();

    // Reviews are behind "See all 17 reviews" and are not reliably present
    // in the initial page text.
    const reviewText=await captureExpediaText(/^(?:See all\s+)?\d+\s+reviews?$/i);
    closeExpediaDialog();

    // Return to Overview so the user's page is left in a normal state.
    const overview=[...document.querySelectorAll("button,a,[role='tab']")]
      .find(el=>/^Overview$/i.test(clean(el.innerText||el.textContent||"")));
    try{overview?.click()}catch{}

    const text=clean(baseText+" "+expandedText+" "+modalText+" "+locationText+" "+policiesText+" "+reviewText);

    const name=first(/Photo gallery for\s+(.+?)\s+Reception/i,baseText) ||
      clean(document.querySelector("h1")?.textContent) ||
      clean(document.title.replace(/\s*\|.*$/,""));

    const dateRange=baseText.match(/Dates\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*([A-Z][a-z]{2,8}\s+\d{1,2})\s*[-–—]\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*([A-Z][a-z]{2,8}\s+\d{1,2})/i)
      || baseText.match(/(?:Start date|Dates)\s+([A-Z][a-z]{2,8}\s+\d{1,2})\s*[-–—]\s*([A-Z][a-z]{2,8}\s+\d{1,2})/i);

    const start=first(/Start date\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*([A-Z][a-z]{2,8}\s+\d{1,2})/i,baseText);
    const end=first(/End date\s+(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun),?\s*([A-Z][a-z]{2,8}\s+\d{1,2})/i,baseText);
    const travelerBlock=first(/(\d+\s+travelers?,\s*\d+\s+room)/i,baseText);
    const adultsMatch=(travelerBlock||"").match(/(\d+)\s+travelers?/i);
    const roomsMatch=(travelerBlock||"").match(/(\d+)\s+room/i);

    const nightlyM=baseText.match(/\$(\d+(?:,\d{3})*(?:\.\d+)?)\s+nightly/i);
    const totalM=baseText.match(/\$(\d+(?:,\d{3})*(?:\.\d+)?)\s+total/i);
    const prevM=baseText.match(/(?:previous price was|previous price)\s+\$(\d+(?:,\d{3})*(?:\.\d+)?)/i);
    const discM=baseText.match(/(\$\d+(?:,\d{3})*(?:\.\d+)?\s+off)/i);
    const n=v=>v==null?null:Number(String(v).replace(/,/g,""));

    return {
      source:"Expedia",url:location.href,scraped_at:new Date().toISOString(),
      property:{
        name,type:/Property class:\s*\d+/i.test(baseText)?"Hotel":"",
        property_class:first(/Property class:\s*(\d+)/i,baseText),
        address:parseAddress(text),rating:parseRating(baseText)
      },
      stay:{
        check_in:dateRange?clean(dateRange[1]):start,
        check_out:dateRange?clean(dateRange[2]):end,
        adults:adultsMatch?Number(adultsMatch[1]):null,
        rooms:roomsMatch?Number(roomsMatch[1]):null,
        traveler_text:travelerBlock
      },
      price:{
        nightly:n(nightlyM?.[1]),total:n(totalM?.[1]),previous:n(prevM?.[1]),
        discount:discM?.[1]||"",currency:"USD"
      },
      rooms:parseRooms(baseText+" "+expandedText),
      dining:{breakfast_available:/Breakfast/i.test(baseText),restaurants:/Restaurant/i.test(baseText)},
      facilities:{amenities:collectAmenities(text),amenity_groups:parseAmenityGroups(text),room_amenities:parseRoomAmenityDetails(expandedText||text)},
      location:{address:parseAddress(text),nearby:parseNearby(text)},
      policies:parsePoliciesClean([policiesText, expandedText, text].filter(Boolean).join(" ")),
      reviews:{
        categories:parseReviewCategories(reviewText||text),
        guest_reviews:parseGuestReviews(reviewText||text)
      },
      highlights:parseHighlights(baseText),
      accessibility:parseAccessibility(text)
    };
  }


chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== "EXPEDIA_SCAN_HOTEL") return;
    scanHotel()
      .then(data => sendResponse({ok: true, data}))
      .catch(error => sendResponse({
        ok: false,
        error: error?.message || String(error)
      }));
    return true;
  });

  window.__expediaScanHotel = scanHotel;
})();