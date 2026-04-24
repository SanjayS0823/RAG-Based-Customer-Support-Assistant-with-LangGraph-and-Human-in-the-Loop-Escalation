const ticketList = document.getElementById("ticket-list");
const ticketCount = document.getElementById("ticket-count");
const refreshTicketsBtn = document.getElementById("refresh-tickets");

function escapeHtml(input) {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

async function loadTickets() {
  const response = await fetch("/api/tickets?status=OPEN");
  if (!response.ok) {
    ticketList.innerHTML = '<p class="muted">Failed to load tickets.</p>';
    ticketCount.textContent = "error";
    return;
  }

  const data = await response.json();
  const tickets = data.tickets || [];
  ticketCount.textContent = `${tickets.length} open`;

  if (tickets.length === 0) {
    ticketList.innerHTML = '<p class="muted">No open escalation tickets.</p>';
    return;
  }

  ticketList.innerHTML = tickets
    .map((ticket) => {
      return `
      <article class="ticket-item" data-ticket-id="${escapeHtml(ticket.ticket_id)}">
        <div class="ticket-head">
          <strong>${escapeHtml(ticket.intent)}</strong>
          <span class="ticket-id">${escapeHtml(ticket.ticket_id)}</span>
        </div>
        <p class="ticket-query">${escapeHtml(ticket.query)}</p>
        <p class="ticket-reason">Reason: ${escapeHtml(ticket.reason)}</p>
        <div class="resolve-row">
          <input class="resolve-input" type="text" placeholder="Write human resolution..." />
          <button type="button" class="resolve-btn">Resolve</button>
        </div>
      </article>
      `;
    })
    .join("");
}

async function resolveTicket(ticketId, humanResponse) {
  const response = await fetch(`/api/tickets/${encodeURIComponent(ticketId)}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ human_response: humanResponse }),
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw new Error(errorBody.detail || "Resolution failed");
  }

  return response.json();
}

refreshTicketsBtn.addEventListener("click", async () => {
  await loadTickets();
});

ticketList.addEventListener("click", async (event) => {
  const button = event.target;
  if (!(button instanceof HTMLElement) || !button.classList.contains("resolve-btn")) {
    return;
  }

  const ticketCard = button.closest(".ticket-item");
  if (!ticketCard) {
    return;
  }

  const ticketId = ticketCard.getAttribute("data-ticket-id");
  const input = ticketCard.querySelector(".resolve-input");
  const humanResponse = input ? String(input.value || "").trim() : "";

  if (!ticketId || humanResponse.length < 3) {
    alert("Add a human response of at least 3 characters.");
    return;
  }

  button.setAttribute("disabled", "true");
  button.textContent = "Resolving...";

  try {
    await resolveTicket(ticketId, humanResponse);
    await loadTickets();
  } catch (error) {
    alert(`Unable to resolve ticket: ${error.message}`);
    button.removeAttribute("disabled");
    button.textContent = "Resolve";
  }
});

loadTickets();
