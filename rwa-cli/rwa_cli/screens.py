from textual.app import ComposeResult
from textual.screen import Screen
from textual.containers import Container, Vertical
from textual.widgets import (
    Header,
    Footer,
    Button,
    Static,
    Select,
    Input,
    TextArea,
    Label,
    Pretty
)
from textual.events import Key
from rich.text import Text
import datetime
import requests
from config import BACKEND_BASE_URL, NFT_VIEW_ROUTE
import logging

# Configure logging
logger = logging.getLogger(__name__)

class MintScreen(Screen):
    """Screen for minting a new RWA NFT."""

    ASSET_TYPES = [
        ("Real Estate", "Real Estate"),
        ("Art", "Art"),
        ("Collectibles", "Collectibles"),
        ("Vehicles", "Vehicles"),
        ("Financial Instruments", "Financial Instruments"),
        ("Commodities", "Commodities")
    ]

    CSS = """
    .form-container {
        height: auto;
        padding: 1;
        border: solid green;
        margin: 1;
    }

    Label {
        margin-bottom: 1;
        margin-top: 1;
    }

    #description {
        height: 5;
        margin-bottom: 1;
        border: solid $accent;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Label("Asset Type"),
                Select(
                    self.ASSET_TYPES,
                    id="asset_type",
                    value="Real Estate"
                ),
                Label("Title"),
                Input(id="title", placeholder="Asset title"),
                Label("Description"),
                TextArea(id="description"),
                Label("Location"),
                Input(id="location", placeholder="Physical location of the asset"),
                Label("Documentation ID"),
                Input(id="documentation_id", placeholder="Legal documentation reference"),
                Container(
                    Button("Cancel", variant="error", id="cancel"),
                    Button("Mint NFT", variant="success", id="submit"),
                    classes="button-row"
                ),
                classes="form-container"
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self.mint_nft()

    def mint_nft(self) -> None:
        """Collect form data and mint the NFT."""
        metadata = {
            "asset_type": self.query_one("#asset_type", Select).value,
            "title": self.query_one("#title", Input).value,
            "description": self.query_one("#description", TextArea).text,
            "location": self.query_one("#location", Input).value,
            "documentation_id": self.query_one("#documentation_id", Input).value,
            "type": "RWA",  # Identify this as a Real World Asset NFT
            "created_at": str(datetime.datetime.now())
        }

        # Validate required fields
        required_fields = ["title", "description", "location", "documentation_id"]
        missing_fields = [field for field in required_fields if not metadata[field]]
        
        if missing_fields:
            self.notify("Please fill in all required fields", severity="error")
            return

        # Return to main screen and trigger NFT minting with metadata
        self.app.pop_screen()
        self.app.mint_nft_with_metadata(metadata) 

class ListNFTScreen(Screen):
    """Screen for listing an NFT for sale."""

    CSS = """
    .form-container {
        height: auto;
        padding: 1;
        border: solid green;
        margin: 1;
    }

    Label {
        margin-bottom: 1;
        margin-top: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, nft_data: dict):
        super().__init__()
        self.nft_data = nft_data

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        metadata = self.nft_data.get('full_metadata', {})
        yield Header()
        yield Container(
            Vertical(
                Label(f"[bold blue]List NFT for Sale[/]"),
                Static(
                    f"[bold green]Title:[/] {metadata.get('title', 'Unknown')}\n"
                    f"[bold green]Type:[/] {metadata.get('asset_type', 'Unknown')}\n"
                    f"[bold green]Location:[/] {metadata.get('location', 'Unknown')}\n"
                    f"[bold green]Documentation ID:[/] {metadata.get('documentation_id', 'Unknown')}"
                ),
                Label("[bold]Enter Sale Price[/]"),
                Input(id="price", placeholder="Enter price in XRP"),
                Container(
                    Button("Cancel", variant="error", id="cancel"),
                    Button("List for Sale", variant="success", id="submit"),
                    classes="button-row"
                ),
                classes="form-container"
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self.list_nft()

    def list_nft(self) -> None:
        """List the NFT for sale."""
        try:
            price = self.query_one("#price", Input).value
            if not price:
                self.notify("Please enter a price", severity="error")
                return
            
            try:
                price_xrp = float(price)
                if price_xrp <= 0:
                    raise ValueError("Price must be positive")
            except ValueError:
                self.notify("Please enter a valid price", severity="error")
                return

            # Pop all screens to return to main screen
            while self.app.screen_stack:
                self.app.pop_screen()
                
            # Trigger NFT listing
            self.app.list_nft_for_sale(self.nft_data, price_xrp)
            
        except Exception as e:
            self.notify(f"Error listing NFT: {str(e)}", severity="error")

class MarketplaceScreen(Screen):
    """Screen for viewing marketplace listings."""

    CSS = """
    .listings-container {
        height: auto;
        padding: 1;
        border: solid blue;
        margin: 1;
        overflow-y: scroll;
    }

    .listing {
        margin: 1;
        padding: 1;
        border: solid green;
        height: auto;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Container(id="listings", classes="listings-container"),
                Container(
                    Button("Refresh", variant="primary", id="refresh"),
                    Button("Back", variant="warning", id="back"),
                    classes="button-row"
                ),
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load listings when screen is mounted."""
        self.load_listings()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id == "refresh":
            self.load_listings()
        elif event.button.id.startswith("buy_"):
            listing_id = event.button.id.replace("buy_", "")
            self.app.buy_nft(listing_id)

    def load_listings(self) -> None:
        """Load and display marketplace listings."""
        self.query_one("#listings").remove_children()
        self.app.load_marketplace_listings(self)

class NFTSelectionScreen(Screen):
    """Screen for selecting an NFT to sell."""

    CSS = """
    .nft-grid {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1 2;
        padding: 1;
        height: auto;
        margin: 1;
    }

    .nft-card {
        width: 100%;
        height: auto;
        border: solid green;
        padding: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    def __init__(self, nfts: list):
        super().__init__()
        self.nfts = nfts

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Label("[bold blue]Select an NFT to sell:[/]"),
                Container(
                    *[self._create_nft_card(nft, i) for i, nft in enumerate(self.nfts)],
                    classes="nft-grid"
                ),
                Container(
                    Button("Back", variant="warning", id="back"),
                    classes="button-row"
                )
            )
        )
        yield Footer()

    def _create_nft_card(self, nft: dict, index: int) -> Container:
        """Create a card widget for an NFT."""
        metadata = nft.get('full_metadata', {})
        return Container(
            Static(
                f"[bold green]{metadata.get('title', 'Untitled')}[/]\n"
                f"Type: {metadata.get('asset_type', 'Unknown')}\n"
                f"Location: {metadata.get('location', 'Unknown')}"
            ),
            Button("Sell This NFT", variant="success", id=f"sell_{index}"),
            classes="nft-card"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back":
            self.app.pop_screen()
        elif event.button.id.startswith("sell_"):
            index = int(event.button.id.replace("sell_", ""))
            self.app.push_screen(ListNFTScreen(self.nfts[index])) 

class TransferScreen(Screen):
    """Screen for transferring an NFT to another address."""

    BINDINGS = [
        ("escape", "app.pop_screen", "Back"),
    ]

    CSS = """
    .form-container {
        height: 100%;
        padding: 1;
        border: solid green;
        margin: 1;
        layout: vertical;
    }

    Label {
        margin-bottom: 1;
        margin-top: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }

    .nft-list {
        height: 1fr;
        margin: 1;
        padding: 1;
        border: solid $accent;
        overflow-y: auto;
    }

    .nft-item {
        margin-bottom: 1;
        padding: 1;
        height: 3;
        border: solid $accent-darken-2;
        layout: horizontal;
    }

    .nft-info {
        width: 3fr;
        height: 100%;
        content-align: left middle;
        padding: 1;
    }

    .nft-button {
        width: 1fr;
        height: 100%;
        align: right middle;
        padding-right: 1;
    }

    .selected {
        border: solid $success;
        background: $success-darken-3;
    }

    .nft-details {
        margin: 1;
        padding: 1;
        height: auto;
        border: solid $warning;
        display: none;
    }

    .nft-details.visible {
        display: block;
    }

    .transfer-controls {
        margin-top: 1;
        height: auto;
        border: solid $accent;
        padding: 1;
    }

    .destination-input {
        width: 100%;
        height: 3;
    }

    .confirmation-dialog {
        width: 60;
        height: auto;
        border: solid $warning;
        padding: 2;
    }

    .loading-container {
        height: 100%;
        align: center middle;
        content-align: center middle;
    }
    """

    def __init__(self):
        super().__init__()
        self.selected_nft = None
        self.selected_nft_data = None
        self.confirmation_mode = False
        self.nfts = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Label("[bold blue]Transfer NFT[/]"),
                Label("[dim]Select an NFT to transfer:[/]"),
                Container(
                    Static("[yellow]Loading NFTs...[/]"),
                    id="nft-list",
                    classes="nft-list"
                ),
                Container(
                    Static(""), # Placeholder for NFT details
                    id="nft-details",
                    classes="nft-details"
                ),
                Container(
                    Vertical(
                        Label("Destination Address"),
                        Input(
                            id="destination",
                            placeholder="Enter destination XRPL address",
                            classes="destination-input"
                        ),
                        Container(
                            Button("Cancel", variant="error", id="cancel"),
                            Button("Transfer", variant="success", id="submit", disabled=True),
                            classes="button-row"
                        ),
                    ),
                    classes="transfer-controls"
                ),
                classes="form-container"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load NFTs when screen is mounted."""
        logger.info("TransferScreen mounted, loading NFTs...")
        self.show_loading()
        self.load_nfts()

    def show_loading(self) -> None:
        """Show loading state."""
        nft_list = self.query_one("#nft-list")
        nft_list.remove_children()
        nft_list.mount(
            Container(
                Static("[yellow]Fetching NFTs from the blockchain...[/]"),
                classes="loading-container"
            )
        )

    def load_nfts(self) -> None:
        """Load user's NFTs."""
        try:
            # Show initial loading message
            nft_list = self.query_one("#nft-list")
            nft_list.remove_children()
            nft_list.mount(Static("[yellow]Fetching NFTs from blockchain...[/]"))

            logger.info("Fetching NFTs from backend...")
            response = requests.get(
                f"{BACKEND_BASE_URL}{NFT_VIEW_ROUTE.format(address=self.app.wallet_data['classic_address'])}"
            )
            
            logger.info(f"Response status code: {response.status_code}")
            if response.status_code != 200:
                self.notify("Failed to load NFTs", severity="error")
                nft_list.remove_children()
                nft_list.mount(Static("[red]Failed to load NFTs[/]"))
                return

            try:
                response_data = response.json()
                logger.info(f"Full response data: {response_data}")
                
                if not isinstance(response_data, dict) or 'nfts' not in response_data:
                    logger.error(f"Invalid response format. Expected dict with 'nfts' key. Got: {type(response_data)}")
                    self.notify("Invalid response format from server", severity="error")
                    nft_list.remove_children()
                    nft_list.mount(Static("[red]Invalid response from server[/]"))
                    return

                self.nfts = response_data.get('nfts', [])
                logger.info(f"Found {len(self.nfts)} NFTs")
                logger.info(f"NFTs data: {self.nfts}")

                # Clear the loading message
                nft_list.remove_children()

                if not self.nfts:
                    nft_list.mount(Static("[yellow]No NFTs found in this wallet[/]"))
                    return

                # Process and display all NFTs
                valid_nfts = []
                for nft in self.nfts:
                    logger.info(f"Processing NFT: {nft}")
                    if not isinstance(nft, dict):
                        logger.warning(f"Invalid NFT data format: {nft}")
                        continue

                    if 'nft_id' not in nft:
                        logger.warning(f"NFT missing nft_id: {nft}")
                        continue

                    # Try both metadata locations
                    metadata = nft.get('metadata', {})
                    if not metadata:
                        metadata = nft.get('full_metadata', {})
                    
                    logger.info(f"NFT metadata: {metadata}")

                    nft_container = Container(
                        Container(
                            Static(
                                f"[bold green]{metadata.get('title', 'Untitled')}[/] "
                                f"([blue]{metadata.get('asset_type', 'Unknown')}[/])\n"
                                f"[dim]ID: {nft['nft_id']}[/]"
                            ),
                            classes="nft-info"
                        ),
                        Container(
                            Button("Select", variant="primary", id=f"select_{nft['nft_id']}"),
                            classes="nft-button"
                        ),
                        classes="nft-item",
                        id=f"container_{nft['nft_id']}"
                    )
                    valid_nfts.append(nft_container)

                # Mount all valid NFTs at once
                for nft_container in valid_nfts:
                    nft_list.mount(nft_container)

            except Exception as json_error:
                logger.error(f"Error processing response: {str(json_error)}")
                self.notify("Error processing server response", severity="error")
                nft_list.remove_children()
                nft_list.mount(Static(f"[red]Error: {str(json_error)}[/]"))
                return

        except Exception as e:
            logger.error(f"Error in load_nfts: {str(e)}")
            self.notify(f"Error loading NFTs: {str(e)}", severity="error")
            nft_list = self.query_one("#nft-list")
            nft_list.remove_children()
            nft_list.mount(Static(f"[red]Error loading NFTs: {str(e)}[/]"))

    def select_nft(self, nft_id: str) -> None:
        """Select an NFT for transfer and show its details."""
        try:
            selected_nft = next((nft for nft in self.nfts if nft['nft_id'] == nft_id), None)
            
            if not selected_nft:
                self.notify("NFT not found", severity="error")
                return

            self.selected_nft = nft_id
            self.selected_nft_data = selected_nft
            self.query_one("#submit").disabled = False

            # Update UI to show selection
            for container in self.query(Container):
                if container.id and container.id.startswith("container_"):
                    if container.id == f"container_{nft_id}":
                        container.add_class("selected")
                    else:
                        container.remove_class("selected")

            # Show NFT details
            details = self.query_one("#nft-details")
            metadata = selected_nft.get('full_metadata', {})
            details_text = (
                f"[bold blue]Selected NFT Details:[/]\n"
                f"[bold green]Title:[/] {metadata.get('title', 'Untitled')}\n"
                f"[bold green]Type:[/] {metadata.get('asset_type', 'Unknown')}\n"
                f"[bold green]Location:[/] {metadata.get('location', 'Unknown')}\n"
                f"[bold green]Documentation ID:[/] {metadata.get('documentation_id', 'Unknown')}\n"
                f"[bold green]Description:[/] {metadata.get('description', 'No description')}\n"
                f"[bold green]NFT ID:[/] {nft_id}\n"
                f"[bold green]Status:[/] {selected_nft.get('status', 'Unknown')}\n"
                f"[bold green]Transaction Hash:[/] {selected_nft.get('transaction_hash', 'Unknown')}"
            )
            details.update(Static(details_text))
            details.add_class("visible")

        except Exception as e:
            logger.error(f"Error selecting NFT: {str(e)}")
            self.notify(f"Error selecting NFT: {str(e)}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            if self.confirmation_mode:
                self._exit_confirmation_mode()
            else:
                self.app.pop_screen()
        elif event.button.id == "submit":
            if self.confirmation_mode:
                self.transfer_nft()
            else:
                self._show_confirmation()
        elif event.button.id.startswith("select_"):
            nft_id = event.button.id.replace("select_", "")
            self.select_nft(nft_id)

    def _show_confirmation(self) -> None:
        """Show transfer confirmation dialog."""
        destination = self.query_one("#destination", Input).value
        
        if not destination:
            self.notify("Please enter a destination address", severity="error")
            return
            
        if not self.selected_nft:
            self.notify("Please select an NFT to transfer", severity="error")
            return

        # Basic XRPL address validation
        if not destination.startswith('r') or len(destination) < 25:
            self.notify("Invalid destination address format", severity="error")
            return

        self.confirmation_mode = True
        metadata = self.selected_nft_data.get('full_metadata', {})
        
        # Create confirmation dialog
        dialog = Container(
            Static(
                f"[bold red]Confirm NFT Transfer[/]\n\n"
                f"You are about to transfer:\n"
                f"[bold green]{metadata.get('title', 'Untitled')}[/]\n"
                f"Type: {metadata.get('asset_type', 'Unknown')}\n"
                f"NFT ID: {self.selected_nft}\n"
                f"To: {destination}\n\n"
                f"[bold yellow]This action cannot be undone![/]"
            ),
            Container(
                Button("Cancel", variant="primary", id="cancel"),
                Button("Confirm Transfer", variant="warning", id="submit"),
                classes="button-row"
            ),
            classes="confirmation-dialog"
        )
        
        self.query_one(".form-container").mount(dialog)

    def _exit_confirmation_mode(self) -> None:
        """Exit confirmation mode."""
        self.confirmation_mode = False
        # Remove confirmation dialog
        for container in self.query(".confirmation-dialog"):
            container.remove()

    def transfer_nft(self) -> None:
        """Transfer the selected NFT."""
        destination = self.query_one("#destination", Input).value
        
        if not destination:
            self.notify("Please enter a destination address", severity="error")
            return
            
        if not self.selected_nft:
            self.notify("Please select an NFT to transfer", severity="error")
            return

        # Return to main screen and trigger NFT transfer
        self.app.pop_screen()
        self.app.transfer_nft(self.selected_nft, destination) 

class WalletSelectionScreen(Screen):
    """Screen for managing and selecting wallets."""

    BINDINGS = [
        ("b", "back", "Back to Menu"),
        ("g", "generate", "Generate Wallet"),
        ("i", "import", "Import Wallet")
    ]

    CSS = """
    Screen {
        align: center middle;
    }

    .wallet-container {
        height: auto;
        max-height: 30;
        padding: 1;
        border: solid green;
        margin: 1;
        width: 150;
    }

    .wallet-list {
        height: auto;
        max-height: 20;
        margin: 1;
        padding: 1;
        border: solid $accent;
        overflow-y: auto;
    }

    .wallet-item {
        margin: 1;
        padding: 1;
        border: solid $accent-darken-2;
        height: auto;
        layout: horizontal;
        align: left middle;
    }

    .wallet-info {
        width: 70%;
        margin-right: 1;
        content-align: left middle;
    }

    .wallet-buttons {
        width: 30%;
        layout: horizontal;
        align: right middle;
        padding-right: 1;
    }

    .wallet-buttons Button {
        margin: 0 1;
        min-width: 10;
    }

    Label {
        margin-bottom: 1;
        margin-top: 1;
        text-align: center;
    }

    .button-row {
        height: auto;
        width: 100%;
        margin-top: 1;
        layout: grid;
        grid-size: 3;
        grid-columns: 1fr 1fr 1fr;
        align: center middle;
    }

    .button-row Button {
        width: 100%;
        margin: 0 1;
        min-height: 3;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Label("[bold blue]Wallet Management[/]"),
                Container(id="wallet-list", classes="wallet-list"),
                Container(
                    Button("Generate New Wallet\n[dim]Create a new wallet[/]", variant="success", id="generate"),
                    Button("Import Existing\n[dim]Import with seed[/]", variant="primary", id="import"),
                    Button("Back to Menu\n[dim]Return to main screen[/]", variant="warning", id="back"),
                    classes="button-row"
                ),
                classes="wallet-container"
            )
        )
        yield Footer()

    def on_mount(self) -> None:
        """Load wallets when screen is mounted."""
        self.load_wallets()

    def load_wallets(self) -> None:
        """Load and display available wallets."""
        try:
            wallets = self.app.load_all_wallets()
            wallet_list = self.query_one("#wallet-list")
            wallet_list.remove_children()

            if not wallets:
                wallet_list.mount(Static("[yellow]No wallets found[/]"))
                return

            current_wallet = self.app.wallet_data.get('classic_address') if self.app.wallet_data else None

            for wallet in wallets:
                is_current = wallet['classic_address'] == current_wallet
                wallet_container = Container(
                    Static(
                        f"[bold {'green' if is_current else 'blue'}]"
                        f"{'[Current] ' if is_current else ''}"
                        f"Address:[/] {wallet['classic_address']}\n",
                        classes="wallet-info"
                    ),
                    Container(
                        Button(
                            "Selected" if is_current else "Select",
                            variant="success" if is_current else "primary",
                            id=f"select_{wallet['classic_address']}",
                            disabled=is_current
                        ),
                        Button(
                            "Remove",
                            variant="error",
                            id=f"remove_{wallet['classic_address']}"
                        ),
                        classes="wallet-buttons"
                    ),
                    classes="wallet-item"
                )
                wallet_list.mount(wallet_container)

        except Exception as e:
            self.notify(f"Error loading wallets: {str(e)}", severity="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "back":
            self.app.pop_screen()
            self.app.refresh_display()  # Ensure display is refreshed after returning
        elif event.button.id == "generate":
            self.app.generate_wallet()
            self.load_wallets()  # Refresh the list
        elif event.button.id == "import":
            self.app.push_screen(ImportWalletScreen())
        elif event.button.id.startswith("select_"):
            address = event.button.id.replace("select_", "")
            self.app.switch_wallet(address)
            self.load_wallets()  # Refresh the list
        elif event.button.id.startswith("remove_"):
            address = event.button.id.replace("remove_", "")
            self.app.remove_wallet(address)
            self.load_wallets()  # Refresh the list

    def on_key(self, event: Key) -> None:
        """Handle key presses."""
        if event.key == "b":
            self.app.pop_screen()
            self.app.refresh_display()
        elif event.key == "g":
            self.app.generate_wallet()
            self.load_wallets()
        elif event.key == "i":
            self.app.push_screen(ImportWalletScreen())

class ImportWalletScreen(Screen):
    """Screen for importing a wallet using a seed."""

    CSS = """
    .form-container {
        height: auto;
        padding: 1;
        border: solid green;
        margin: 1;
    }

    Label {
        margin-bottom: 1;
        margin-top: 1;
    }

    .button-row {
        height: auto;
        align: center middle;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the screen."""
        yield Header()
        yield Container(
            Vertical(
                Label("[bold blue]Import Wallet[/]"),
                Label("Wallet Seed"),
                Input(id="seed", placeholder="Enter your wallet seed", password=True),
                Container(
                    Button("Cancel", variant="error", id="cancel"),
                    Button("Import", variant="success", id="submit"),
                    classes="button-row"
                ),
                classes="form-container"
            )
        )
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "cancel":
            self.app.pop_screen()
        elif event.button.id == "submit":
            self.import_wallet()

    def import_wallet(self) -> None:
        """Import a wallet using the provided seed."""
        seed = self.query_one("#seed", Input).value
        
        if not seed:
            self.notify("Please enter a wallet seed", severity="error")
            return

        try:
            self.app.import_wallet(seed)
            self.app.pop_screen()  # Return to wallet selection screen
        except Exception as e:
            self.notify(f"Error importing wallet: {str(e)}", severity="error") 