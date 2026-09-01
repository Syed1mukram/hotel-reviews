let latest = null;
let currentTab = "overview";

function activeTab() {
  return chrome.tabs.query({active:true,currentWindow:true}).then(t => t[0]);
}
function esc(v) {
  return String(v ?? "").replace(/[&<>"']/g, x => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"
  }[x]));
}
function val(v) {
  return v === null || v === undefined || v === "" ? "—" : esc(v);
}
function card(title, html) {
  return `<section class="card"><h2>${esc(title)}</h2>${html}</section>`;
}
function item(label, value) {
  return `<div class="item"><div class="label">${esc(label)}</div><div class="value">${val(value)}</div></div>`;
}
function badges(arr) {
  if (!arr?.length) return '<div class="muted">No data found</div>';
  return `<div class="badges">${arr.map(x=>`<span class="badge">${esc(x)}`).join("")}</div>`;
}
function render() {
  const c = document.getElementById("content");
  if (!latest) {
    c.innerHTML = '<div class="empty">Scan an Expedia hotel page.</div>';
    return;
  }
  const p = latest.property || {};
  const r = p.rating || {};
  document.getElementById("hotelTitle").textContent = p.name || "Hotel Research";
  document.getElementById("subTitle").textContent =
    `${r.score ?? "—"}/10 · ${r.reviews ?? "—"} reviews`;

  if (currentTab === "overview") {
    const price=latest.price||{}, stay=latest.stay||{};
    c.innerHTML =
      card("Property", `<div class="grid">
        ${item("Name",p.name)}${item("Type",p.type)}
        ${item("Class",p.property_class ? p.property_class+" star" : "")}
        ${item("Rating",r.score ? `${r.score}/10 ${r.label||""}` : "")}
        ${item("Reviews",r.reviews)}
        ${item("Address",p.address)}
      </div>`) +
      card("Stay & Price", `<div class="grid">
        ${item("Check-in",stay.check_in)}${item("Check-out",stay.check_out)}
        ${item("Guests",stay.adults)}${item("Rooms",stay.rooms)}
        ${item("Nightly",price.nightly != null ? `$${price.nightly}` : "")}
        ${item("Total",price.total != null ? `$${price.total}` : "")}
        ${item("Previous",price.previous != null ? `$${price.previous}` : "")}
        ${item("Discount",price.discount)}
      </div>`) +
      card("Highlights",badges(latest.highlights||[]));
  }

  if (currentTab === "rooms") {
    const rooms=latest.rooms||[];
    c.innerHTML=rooms.length ? rooms.map((x,i)=>card(x.name||`Room ${i+1}`,
      `<div class="grid">
        ${item("Size",x.size_sq_ft ? x.size_sq_ft+" sq ft" : "")}
        ${item("Sleeps",x.sleeps)}${item("Bedrooms",x.bedrooms)}
        ${item("Bed",x.bed)}
        ${item("Nightly",x.nightly_price != null ? "$"+x.nightly_price : "")}
        ${item("Total",x.total_price != null ? "$"+x.total_price : "")}
        ${item("Previous",x.previous_price != null ? "$"+x.previous_price : "")}
        ${item("Breakfast",x.breakfast_extra != null ? "$"+x.breakfast_extra+" extra" : "")}
        ${item("Cancellation",x.cancellation)}
      </div><div style="margin-top:8px">${badges(x.amenities||[])}</div>`)).join("")
      : '<div class="empty">No rooms found.</div>';
  }

  if (currentTab === "reviews") {
    const cats=latest.reviews?.categories||[], reviews=latest.reviews?.guest_reviews||[];
    c.innerHTML =
      card("Category Scores",cats.length ? `<div class="grid">${cats.map(x=>item(x.category,`${x.score}/${x.out_of}`)).join("")}</div>`:'<div class="muted">No category scores found.</div>')+
      card("Guest Reviews",reviews.length ? reviews.map(x=>`<div class="review"><div class="score">${x.score}/${x.out_of} · ${esc(x.sentiment)}</div><div>${esc(x.comment)}</div></div>`).join(""):'<div class="muted">No guest reviews found.</div>');
  }

  if (currentTab === "facilities") {
    const a=latest.facilities?.amenities||[], g=latest.facilities?.amenity_groups||{};
    const labels={internet:"Internet",parking:"Parking",family:"Family friendly",conveniences:"Conveniences",guest_services:"Guest services",business_services:"Business services",accessibility:"Accessibility",other:"Other useful facilities"};
    let h=card("Amenities",badges(a));
    for(const [k,label] of Object.entries(labels)) if(g[k]?.length) h+=card(label,badges(g[k]));
    c.innerHTML=h;
  }

  if (currentTab === "location") {
    const nearby=latest.location?.nearby||[];
    c.innerHTML=card("Address",`<div>${val(latest.location?.address||p.address)}</div>`)+
      card("Nearby",nearby.length?nearby.map(x=>`<div class="item" style="margin-bottom:5px"><b>${esc(x.name)}</b><br><span class="muted">${esc(x.distance)}</span></div>`).join(""):'<div class="muted">No nearby places found.</div>');
  }

  if (currentTab === "policies") {
    const x=latest.policies||{};
    c.innerHTML=card("Policies",`<div class="grid">
      ${item("Check-in",x.check_in)}${item("Check-in end",x.check_in_end)}
      ${item("Minimum age",x.minimum_check_in_age)}${item("Check-out",x.check_out)}
      ${item("Pets",x.pets)}${item("Children",x.children)}
      ${item("Rollaway",x.rollaway_extra_bed)}${item("Cribs",x.cribs)}
      ${item("Payment",x.payment)}${item("Cancellation",x.cancellation)}
    </div>`);
  }
}

async function scan() {
  const status=document.getElementById("status");
  const button=document.getElementById("scan");
  status.textContent="Scanning Expedia page...";
  button.disabled=true;
  try {
    const tab=await activeTab();
    if(!tab?.id || !/^https:\/\/([^.]+\.)?expedia\.com\//i.test(tab.url||""))
      throw new Error("Open an Expedia hotel page first.");

    let response;
    try {
      response = await chrome.tabs.sendMessage(tab.id, {type:"EXPEDIA_SCAN_HOTEL"});
    } catch (firstError) {
      // The page may have been opened before the extension was reloaded.
      // Inject the content script once, then retry the message.
      await chrome.scripting.executeScript({
        target:{tabId:tab.id},
        files:["content.js"]
      });
      response = await chrome.tabs.sendMessage(tab.id, {type:"EXPEDIA_SCAN_HOTEL"});
    }

    if (!response?.ok) {
      throw new Error(response?.error || "No hotel data returned.");
    }
    latest=response.data;
    if(!latest) throw new Error("No hotel data returned.");
    status.textContent="Scan complete.";
    render();
  } catch(e) {
    console.error(e);
    status.textContent=e?.message||String(e);
  } finally {
    button.disabled=false;
  }
}

function csvEscape(v){return `"${String(v??"").replace(/"/g,'""')}"`;}
function flatten(obj,prefix="",out={}){
  if(Array.isArray(obj)) out[prefix]=obj.map(x=>typeof x==="object"?JSON.stringify(x):x).join(" | ");
  else if(obj&&typeof obj==="object") for(const [k,v] of Object.entries(obj)) flatten(v,prefix?prefix+"."+k:k,out);
  else out[prefix]=obj;
  return out;
}
async function copyAll(){
  if(!latest)return;
  const b=document.getElementById("copyAll"), original=b.textContent;
  try{await navigator.clipboard.writeText(JSON.stringify(latest,null,2));}
  catch(e){const ta=document.createElement("textarea");ta.value=JSON.stringify(latest,null,2);ta.style.position="fixed";ta.style.opacity="0";document.body.appendChild(ta);ta.select();document.execCommand("copy");ta.remove();}
  b.textContent="✓ COPIED";b.classList.add("copied");document.getElementById("status").textContent="All hotel data copied.";
  clearTimeout(window.__copyTimer);window.__copyTimer=setTimeout(()=>{b.textContent=original;b.classList.remove("copied");},1800);
}
function download(name,content,type){const blob=new Blob([content],{type}),u=URL.createObjectURL(blob),a=document.createElement("a");a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),500);}
function downloadJson(){if(latest)download("hotel-research.json",JSON.stringify(latest,null,2),"application/json");}
function downloadCsv(){if(latest){const row=flatten(latest),keys=Object.keys(row);download("hotel-research.csv",keys.map(csvEscape).join(",")+"\n"+keys.map(k=>csvEscape(row[k])).join(","),"text/csv");}}

document.addEventListener("DOMContentLoaded",()=>{
  document.getElementById("scan").addEventListener("click",scan);
  document.getElementById("copyAll").addEventListener("click",copyAll);
  document.getElementById("downloadJson").addEventListener("click",downloadJson);
  document.getElementById("downloadCsv").addEventListener("click",downloadCsv);
  document.querySelectorAll("#tabs button").forEach(b=>b.addEventListener("click",()=>{
    document.querySelectorAll("#tabs button").forEach(x=>x.classList.remove("active"));
    b.classList.add("active");currentTab=b.dataset.tab;render();
  }));
  render();
});
