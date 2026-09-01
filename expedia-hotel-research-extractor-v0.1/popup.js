let latest = null;

function activeTab() {
  return chrome.tabs.query({active: true, currentWindow: true}).then(tabs => tabs[0]);
}

async function scan() {
  const status = document.getElementById("status");
  const result = document.getElementById("result");
  const actions = document.getElementById("actions");

  status.textContent = "Scanning Expedia page...";
  result.textContent = "";
  actions.classList.add("hidden");

  try {
    const tab = await activeTab();
    if (!tab || !tab.id || !/^https:\/\/([^.]+\.)?expedia\.com\//i.test(tab.url || "")) {
      throw new Error("Open an Expedia hotel/accommodation page first.");
    }

    const response = await chrome.tabs.sendMessage(tab.id, {type: "SCAN_HOTEL"});
    if (!response || !response.data) throw new Error("No hotel data returned.");

    latest = response.data;
    result.textContent = JSON.stringify(latest, null, 2);
    status.textContent = "Scan complete.";
    actions.classList.remove("hidden");
  } catch (e) {
    status.textContent = e.message || String(e);
  }
}

document.getElementById("scan").addEventListener("click", scan);

document.getElementById("copyJson").addEventListener("click", async () => {
  if (!latest) return;
  await navigator.clipboard.writeText(JSON.stringify(latest, null, 2));
  document.getElementById("status").textContent = "JSON copied.";
});

document.getElementById("downloadJson").addEventListener("click", () => {
  if (!latest) return;
  const blob = new Blob([JSON.stringify(latest, null, 2)], {type:"application/json"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${(latest.property.name || "hotel").replace(/[^a-z0-9]+/gi,"-").toLowerCase()}.json`;
  a.click();
  URL.revokeObjectURL(url);
});
