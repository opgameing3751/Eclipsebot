#Ticket globale 
from src.imports import *

version = "0.1"
load_dotenv("data/config/config.env")
TICKET_CREATE_CHANNEL = os.getenv("Ticket_channel")




class TicketManager:
    def __init__(self, file_path="data/ticket/opentickets.json"):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.file_path.exists():
            self.file_path.write_text("{}", encoding="utf-8")

        self.tickets = self.load()

    def load(self):
        """Load all open tickets from the JSON file."""
        with open(self.file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("Invalid ticket JSON format.")

        return data

    def save(self):
        """Save all open tickets to the JSON file."""
        temp_path = self.file_path.with_suffix(".json.tmp")

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(self.tickets, file, indent=4, ensure_ascii=False)

        os.replace(temp_path, self.file_path)

    def create_ticket(self, user_id, username, guild_id=None, channel_id=None):
        """Create a ticket with Username-RandomString as its ID."""

        safe_username = re.sub(r"[^a-zA-Z0-9_-]", "_", username)
        safe_username = safe_username[:32] or "user"

        while True:
            random_string = secrets.token_hex(3)
            ticket_id = f"{safe_username}-{random_string}"

            if ticket_id not in self.tickets:
                break

        ticket = {
            "id": ticket_id,
            "user_id": str(user_id),
            "username": username,
            "guild_id": str(guild_id) if guild_id is not None else None,
            "channel_id": str(channel_id) if channel_id is not None else None,
            "opened_at": datetime.now(timezone.utc).isoformat(),
            "status": "open"
        }

        self.tickets[ticket_id] = ticket
        self.save()

        return ticket.copy()

    def close_ticket(self, ticket_id):
        """Close and remove an open ticket."""
        ticket = self.tickets.pop(ticket_id, None)

        if ticket is None:
            return None

        self.save()
        return ticket.copy()

    def get_ticket(self, ticket_id):
        """Retrieve ticket information using its ID."""
        ticket = self.tickets.get(ticket_id)
        return ticket.copy() if ticket else None

    def get_user_tickets(self, user_id):
        """Get all open tickets belonging to a Discord user."""
        return [
            ticket.copy()
            for ticket in self.tickets.values()
            if ticket["user_id"] == str(user_id)
        ]

    def get_open_tickets(self):
        """Retrieve every open ticket."""
        return [ticket.copy() for ticket in self.tickets.values()]

    def update_ticket(self, ticket_id, **kwargs):
        """Modify a ticket using its ID."""
        ticket = self.tickets.get(ticket_id)

        if ticket is None:
            return None

        protected = {"id", "user_id", "username", "opened_at", "status"}

        if protected.intersection(kwargs):
            raise ValueError("Cannot modify protected ticket fields.")

        ticket.update(kwargs)
        ticket["updated_at"] = datetime.now(timezone.utc).isoformat()

        self.save()
        return ticket.copy()
    
tickets = TicketManager()
print("loaded Tickets")