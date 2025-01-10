from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Button, Static, Pretty
from textual.screen import Screen
from textual import work
import requests
import json
import os
import logging
import uuid
import datetime
from rich.text import Text
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.transactions import NFTokenMint, NFTokenCreateOffer
from xrpl.models.requests import AccountInfo
from xrpl.utils import str_to_hex
from xrpl.transaction import sign
from xrpl.core import binarycodec
from screens import MintScreen, TransferScreen, WalletSelectionScreen, ImportWalletScreen
from config import *

# Configure logging
logging.basicConfig(
    filename='log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class WalletDisplay(Static):
    """Display wallet information with balance."""
    
    DEFAULT_CSS = """
    WalletDisplay {
        height: auto;
        margin: 1;
        padding: 1;
        border: solid green;
        min-width: 50;
    }
    """
    
    def compose(self) -> ComposeResult:
        """Create child widgets for the display."""
        yield Static(id="wallet-info")
        yield Static(id="balance-info")
    
    def update_info(self, wallet_data=None):
        """Update wallet information display."""
        if not wallet_data:
            self.query_one("#wallet-info").update("[yellow]No wallet found. Generate one first.[/]")
            self.query_one("#balance-info").update("")
            return

        self.query_one("#wallet-info").update(
            f"[bold blue]Wallet Address:[/] {wallet_data['classic_address']}\n"
            f"[bold blue]Explorer:[/] https://testnet.xrpl.org/accounts/{wallet_data['classic_address']}"
        )
        self.query_one("#balance-info").update("[yellow]Fetching balance...[/]")

    def update_balance(self, balance: float):
        """Update balance display."""
        self.query_one("#balance-info").update(f"[bold green]Balance:[/] {balance} XRP")

class ResultDisplay(Static):
    """Display operation results."""
    
    DEFAULT_CSS = """
    ResultDisplay {
        height: auto;
        min-height: 10;
        margin: 1;
        padding: 1;
        border: solid blue;
        min-width: 50;
    }
    """
    
    def show_result(self, data):
        if isinstance(data, dict):
            self.update(Pretty(data))
        else:
            self.update(Text(str(data)))

class NFTApp(App):
    """XRPL NFT Management Application"""
    
    CSS = """
    Screen {
        align: center middle;
    }

    Button {
        margin: 1 2;
    }

    .button-row {
        align: center middle;
        height: auto;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh Balance"),
        ("g", "generate", "Generate Wallet"),
        ("m", "mint", "Mint NFT"),
        ("v", "view", "View NFTs"),
        ("t", "transfer", "Transfer NFT"),
        ("s", "switch", "Switch Wallet"),
        ("b", "back", "Back to Menu")
    ]

    def __init__(self):
        super().__init__()
        # Create wallets directory if it doesn't exist
        os.makedirs(WALLETS_DIR, exist_ok=True)
        self.wallet_data = self.load_current_wallet()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield WalletDisplay(id="wallet-display")
        yield Container(
            Horizontal(
                Button("Generate Wallet", variant="primary", id="generate"),
                Button("Switch Wallet", variant="warning", id="switch"),
                Button("Refresh Balance", variant="warning", id="refresh"),
                Button("Mint NFT", variant="success", id="mint"),
                Button("View NFTs", variant="warning", id="view"),
                Button("Transfer NFT", variant="primary", id="transfer"),
                Button("Back", variant="default", id="back"),
                classes="button-row"
            )
        )
        yield ResultDisplay(id="result-display")
        yield Footer()

    def on_mount(self) -> None:
        """Refresh wallet info when app starts."""
        self.refresh_display()

    def refresh_display(self):
        """Refresh all display elements."""
        try:
            wallet_display = self.query_one("#wallet-display")
            if wallet_display:
                wallet_display.update_info(self.wallet_data)
                if self.wallet_data:
                    self.get_balance()
        except Exception as e:
            logger.error(f"Error refreshing display: {str(e)}")

    @work(thread=True)
    def get_balance(self):
        """Get wallet balance in a separate thread."""
        try:
            # Create a new client for each request
            client = JsonRpcClient(XRPL_TESTNET_URL)
            
            # Create proper XRPL request model
            request = AccountInfo(
                account=self.wallet_data["classic_address"],
                ledger_index="validated",
                strict=True
            )
            logger.info(f"Creating balance request for {self.wallet_data['classic_address']}")
            try:
                response = client.request(request)
                logger.info(f"Raw response: {json.dumps(response.result, indent=2)}")
            except Exception as req_error:
                logger.error(f"Request failed: {str(req_error)}")
                raise
            
            if response.is_successful():
                balance = int(response.result["account_data"]["Balance"])
                balance_xrp = balance / 1_000_000
                logger.info(f"Balance fetched: {balance_xrp} XRP")
                def update_ui():
                    try:
                        wallet_display = self.query_one("#wallet-display", WalletDisplay)
                        if wallet_display:
                            wallet_display.update_balance(balance_xrp)
                    except Exception as ui_error:
                        logger.error(f"Error updating wallet display: {str(ui_error)}")
                
                self.call_from_thread(update_ui)
            else:
                logger.error(f"Failed to get balance. Response: {json.dumps(response.result, indent=2)}")
                def show_error():
                    try:
                        wallet_display = self.query_one("#wallet-display", WalletDisplay)
                        if wallet_display:
                            wallet_display.update_balance(0)
                    except Exception as ui_error:
                        logger.error(f"Error updating wallet display: {str(ui_error)}")
                
                self.call_from_thread(show_error)
        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            def show_error():
                try:
                    wallet_display = self.query_one("#wallet-display", WalletDisplay)
                    if wallet_display:
                        wallet_display.update_balance(0)
                except Exception as ui_error:
                    logger.error(f"Error updating wallet display: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    def load_current_wallet(self):
        """Load the currently selected wallet."""
        try:
            if os.path.exists(CURRENT_WALLET_FILE):
                with open(CURRENT_WALLET_FILE, "r") as f:
                    current = json.load(f)
                    wallet_file = os.path.join(WALLETS_DIR, f"{current['address']}.json")
                    if os.path.exists(wallet_file):
                        with open(wallet_file, "r") as wf:
                            return json.load(wf)
            return None
        except Exception as e:
            logger.error(f"Error loading current wallet: {str(e)}")
            return None

    def save_current_wallet(self, address: str):
        """Save the current wallet selection."""
        try:
            with open(CURRENT_WALLET_FILE, "w") as f:
                json.dump({"address": address}, f)
        except Exception as e:
            logger.error(f"Error saving current wallet selection: {str(e)}")

    def load_all_wallets(self):
        """Load all available wallets."""
        wallets = []
        try:
            for filename in os.listdir(WALLETS_DIR):
                if filename.endswith(".json"):
                    with open(os.path.join(WALLETS_DIR, filename), "r") as f:
                        wallet = json.load(f)
                        wallets.append(wallet)
            return wallets
        except Exception as e:
            logger.error(f"Error loading wallets: {str(e)}")
            return []

    def save_wallet(self, wallet):
        """Save a wallet to the wallets directory."""
        try:
            wallet_data = {
                "classic_address": wallet.classic_address,
                "seed": wallet.seed
            }
            wallet_file = os.path.join(WALLETS_DIR, f"{wallet.classic_address}.json")
            with open(wallet_file, "w") as f:
                json.dump(wallet_data, f)
            
            # If this is the first wallet, make it the current wallet
            if not self.wallet_data:
                self.save_current_wallet(wallet.classic_address)
                self.wallet_data = wallet_data
            
            return wallet_data
        except Exception as e:
            logger.error(f"Error saving wallet: {str(e)}")
            return None

    @work(thread=True)
    def switch_wallet(self, address: str):
        """Switch to a different wallet."""
        try:
            wallet_file = os.path.join(WALLETS_DIR, f"{address}.json")
            if not os.path.exists(wallet_file):
                raise Exception("Wallet not found")
            
            with open(wallet_file, "r") as f:
                self.wallet_data = json.load(f)
            self.save_current_wallet(address)
            
            # Update UI safely from the thread
            def update_ui():
                try:
                    self.refresh_display()
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[green]Wallet switched successfully![/]")
                except Exception as ui_error:
                    logger.error(f"Error updating UI after wallet switch: {str(ui_error)}")
            
            self.call_from_thread(update_ui)
            
        except Exception as e:
            logger.error(f"Error switching wallet: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error switching wallet: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    @work(thread=True)
    def remove_wallet(self, address: str):
        """Remove a wallet from the system."""
        try:
            wallet_file = os.path.join(WALLETS_DIR, f"{address}.json")
            if not os.path.exists(wallet_file):
                raise Exception("Wallet not found")
            
            # If removing current wallet, clear current selection
            if self.wallet_data and self.wallet_data["classic_address"] == address:
                self.wallet_data = None
                if os.path.exists(CURRENT_WALLET_FILE):
                    os.remove(CURRENT_WALLET_FILE)
            
            os.remove(wallet_file)
            
            # Update UI safely from the thread
            def update_ui():
                try:
                    self.refresh_display()
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[green]Wallet removed successfully![/]")
                except Exception as ui_error:
                    logger.error(f"Error updating UI after wallet removal: {str(ui_error)}")
            
            self.call_from_thread(update_ui)
            
        except Exception as e:
            logger.error(f"Error removing wallet: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error removing wallet: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    @work(thread=True)
    def import_wallet(self, seed: str):
        """Import a wallet using its seed."""
        try:
            wallet = Wallet.from_seed(seed)
            self.wallet_data = self.save_wallet(wallet)
            self.save_current_wallet(wallet.classic_address)
            
            # Update UI safely from the thread
            def update_ui():
                try:
                    self.refresh_display()
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[green]Wallet imported successfully![/]\nAddress: {wallet.classic_address}")
                except Exception as ui_error:
                    logger.error(f"Error updating UI after wallet import: {str(ui_error)}")
            
            self.call_from_thread(update_ui)
            
        except Exception as e:
            logger.error(f"Error importing wallet: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error importing wallet: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)
            raise

    def action_switch(self):
        """Show the wallet selection screen."""
        self.push_screen(WalletSelectionScreen())

    def action_generate(self):
        """Generate a new wallet."""
        self.generate_wallet()

    def action_refresh(self):
        """Refresh wallet balance."""
        if self.wallet_data:
            self.get_balance()

    def action_mint(self):
        """Show the mint NFT form screen."""
        if self.wallet_data:
            self.push_screen(MintScreen())
        else:
            try:
                result_display = self.query_one("#result-display", ResultDisplay)
                if result_display:
                    result_display.update("[red]No wallet found. Generate one first.[/]")
            except Exception as e:
                logger.debug(f"No result display found when showing mint error: {str(e)}")

    def action_view(self):
        """View NFTs."""
        if self.wallet_data:
            self.view_nfts()
        else:
            try:
                result_display = self.query_one("#result-display", ResultDisplay)
                if result_display:
                    result_display.update("[red]No wallet found. Generate one first.[/]")
            except Exception as e:
                logger.debug(f"No result display found when showing view error: {str(e)}")

    def action_transfer(self):
        """Show the transfer NFT form screen."""
        if self.wallet_data:
            self.push_screen(TransferScreen())
        else:
            try:
                result_display = self.query_one("#result-display", ResultDisplay)
                if result_display:
                    result_display.update("[red]No wallet found. Generate one first.[/]")
            except Exception as e:
                logger.debug(f"No result display found when showing transfer error: {str(e)}")

    def action_back(self):
        """Return to base menu."""
        self.refresh_display()
        try:
            result_display = self.query_one("#result-display", ResultDisplay)
            if result_display:
                result_display.update("")
        except Exception as e:
            logger.debug(f"No result display found when going back: {str(e)}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "generate":
            self.action_generate()
        elif event.button.id == "switch":
            self.action_switch()
        elif event.button.id == "refresh":
            self.action_refresh()
        elif event.button.id == "mint":
            self.action_mint()
        elif event.button.id == "view":
            self.action_view()
        elif event.button.id == "transfer":
            self.action_transfer()
        elif event.button.id == "back":
            self.action_back()

    @work(thread=True)
    def generate_wallet(self):
        """Generate and fund a new wallet."""
        try:
            def show_creating():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[yellow]Creating new wallet...[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing creating message: {str(ui_error)}")
            
            self.call_from_thread(show_creating)
            
            wallet = Wallet.create()
            response = requests.post(
                "https://faucet.altnet.rippletest.net/accounts",
                json={"destination": wallet.classic_address}
            )
            
            if response.status_code != 200:
                raise Exception("Failed to fund wallet from faucet")
            
            self.wallet_data = self.save_wallet(wallet)
            logger.info(f"Wallet generated: {wallet.classic_address}")
            
            def update_ui():
                try:
                    self.refresh_display()
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(
                            f"[green]Wallet created successfully![/]\nAddress: {wallet.classic_address}\nSeed: {wallet.seed}"
                        )
                except Exception as ui_error:
                    logger.error(f"Error updating UI after wallet generation: {str(ui_error)}")
            
            self.call_from_thread(update_ui)
            
        except Exception as e:
            logger.error(f"Error generating wallet: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Failed to create wallet: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    @work(thread=True)
    def mint_nft(self, wallet, uri, metadata=None):
        """Mint an NFT."""
        try:
            def show_preparing():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[yellow]Preparing to mint NFT...[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing preparing message: {str(ui_error)}")
            
            self.call_from_thread(show_preparing)
            
            # Get current sequence number
            client = JsonRpcClient(XRPL_TESTNET_URL)
            seq_request = AccountInfo(
                account=wallet["classic_address"],
                ledger_index="validated",
                strict=True
            )
            seq_response = client.request(seq_request)
            if not seq_response.is_successful():
                raise Exception("Failed to get account sequence")
            
            current_sequence = seq_response.result["account_data"]["Sequence"]
            logger.info(f"Got sequence number: {current_sequence}")
            
            # Get template
            template_data = {
                "account": wallet["classic_address"],
                "uri": uri,
                "flags": 8,
                "transfer_fee": 0,
                "taxon": 0,
                "metadata": metadata or {
                    "source": "RWA CLI",
                    "version": "1.0"
                }
            }
            
            template_response = requests.post(
                f"{BACKEND_BASE_URL}{MINT_TEMPLATE_ROUTE}",
                json=template_data
            )
            
            if template_response.status_code != 200:
                raise Exception(f"Failed to get template: {template_response.json().get('error')}")
            
            template = template_response.json()["template"]["template"]
            
            # Create and sign transaction
            mint_tx = NFTokenMint(
                account=template["account"],
                uri=template["uri"],
                flags=template["flags"],
                transfer_fee=template["transfer_fee"],
                nftoken_taxon=template["nftoken_taxon"],
                sequence=current_sequence,
                fee="10"  # Standard fee in drops
            )
            
            wallet_instance = Wallet.from_seed(wallet["seed"])
            signed_tx = sign(mint_tx, wallet_instance)
            tx_blob = binarycodec.encode(signed_tx.to_xrpl())
            
            # Submit transaction
            submit_data = {
                "signed_transaction": {
                    "tx_blob": tx_blob,
                    "hash": signed_tx.get_hash(),
                    "sequence": current_sequence,
                    "account": wallet["classic_address"]
                },
                "account": wallet["classic_address"],
                "uri": uri,
                "metadata": template_data["metadata"]
            }
            
            logger.info(f"Submitting transaction with sequence {current_sequence}")
            submit_response = requests.post(
                f"{BACKEND_BASE_URL}{SUBMIT_TRANSACTION_ROUTE}",
                json=submit_data
            )
            
            if submit_response.status_code != 200:
                error_msg = submit_response.json().get('error', '')
                if "duplicate key error" in error_msg:
                    logger.warning("NFT minted successfully but failed to track in database")
                    def show_success_warning():
                        try:
                            result_display = self.query_one("#result-display", ResultDisplay)
                            if result_display:
                                result_display.update(
                                    "[green]NFT minted successfully on XRPL![/]\n[yellow]Warning: Failed to track NFT in backend database[/]"
                                )
                        except Exception as ui_error:
                            logger.error(f"Error showing success warning: {str(ui_error)}")
                    
                    self.call_from_thread(show_success_warning)
                    return
                raise Exception(f"Failed to submit: {error_msg}")
            
            result = submit_response.json()
            def show_success():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[green]NFT minted successfully![/]\n{Pretty(result)}")
                except Exception as ui_error:
                    logger.error(f"Error showing success message: {str(ui_error)}")
            
            self.call_from_thread(show_success)
            
        except Exception as e:
            logger.error(f"Error minting NFT: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error minting NFT: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    @work(thread=True)
    def view_nfts(self):
        """View NFTs for current wallet."""
        try:
            def show_fetching():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[yellow]Fetching NFTs...[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing fetching message: {str(ui_error)}")
            
            self.call_from_thread(show_fetching)
            
            response = requests.get(
                f"{BACKEND_BASE_URL}{NFT_VIEW_ROUTE.format(address=self.wallet_data['classic_address'])}"
            )
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch NFTs: {response.json().get('error')}")
            
            nfts_data = response.json()
            nfts = nfts_data.get('nfts', [])
            
            if not nfts:
                def show_no_nfts():
                    try:
                        result_display = self.query_one("#result-display", ResultDisplay)
                        if result_display:
                            result_display.update("[yellow]No NFTs found for this wallet[/]")
                    except Exception as ui_error:
                        logger.error(f"Error showing no NFTs message: {str(ui_error)}")
                
                self.call_from_thread(show_no_nfts)
                return
            
            # Format NFTs into a readable display
            nft_display = "[bold blue]Your NFTs:[/]\n\n"
            for i, nft in enumerate(nfts, 1):
                nft_display += f"[bold green]NFT #{i}[/]\n"
                nft_display += f"URI: {nft.get('uri', 'N/A')}\n"
                nft_display += f"Transaction Hash: {nft.get('transaction_hash', 'N/A')}\n"
                nft_display += f"Status: {nft.get('status', 'N/A')}\n"
                if nft.get('metadata'):
                    nft_display += "Metadata:\n"
                    for key, value in nft['metadata'].items():
                        nft_display += f"  {key}: {value}\n"
                nft_display += "\n"
            
            def show_nfts():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(Text.from_markup(nft_display))
                except Exception as ui_error:
                    logger.error(f"Error showing NFTs: {str(ui_error)}")
            
            self.call_from_thread(show_nfts)
            
        except Exception as e:
            logger.error(f"Error viewing NFTs: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error viewing NFTs: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

    def mint_nft_with_metadata(self, metadata: dict):
        """Mint an NFT with the provided metadata."""
        if not self.wallet_data:
            return
        
        # Generate IPFS-style URI with metadata
        uri = f"ipfs://QmRWA{uuid.uuid4().hex}"  # Placeholder URI, should be real IPFS in production
        
        # Start the minting process with metadata
        self.mint_nft(self.wallet_data, uri, metadata)

    @work(thread=True)
    def transfer_nft(self, nft_id: str, destination: str):
        """Transfer an NFT to another address."""
        try:
            def show_preparing():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update("[yellow]Preparing NFT transfer...[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing preparing message: {str(ui_error)}")
            
            self.call_from_thread(show_preparing)
            
            # Get current sequence number
            client = JsonRpcClient(XRPL_TESTNET_URL)
            seq_request = AccountInfo(
                account=self.wallet_data["classic_address"],
                ledger_index="validated",
                strict=True
            )
            seq_response = client.request(seq_request)
            if not seq_response.is_successful():
                raise Exception("Failed to get account sequence")
            
            current_sequence = seq_response.result["account_data"]["Sequence"]
            logger.info(f"Got sequence number: {current_sequence}")
            
            # Create NFT offer transaction
            offer_tx = NFTokenCreateOffer(
                account=self.wallet_data["classic_address"],
                nftoken_id=nft_id,
                destination=destination,
                amount="0",  # 0 for a transfer (not a sale)
                flags=1,  # tfSellNFToken flag
                sequence=current_sequence,
                fee="10"  # Standard fee in drops
            )
            
            # Sign the transaction
            wallet_instance = Wallet.from_seed(self.wallet_data["seed"])
            signed_tx = sign(offer_tx, wallet_instance)
            tx_blob = binarycodec.encode(signed_tx.to_xrpl())
            
            # Submit the transaction
            submit_data = {
                "signed_transaction": {
                    "tx_blob": tx_blob,
                    "hash": signed_tx.get_hash(),
                    "sequence": current_sequence,
                    "account": self.wallet_data["classic_address"]
                },
                "account": self.wallet_data["classic_address"],
                "destination": destination
            }
            
            logger.info(f"Submitting transfer transaction with sequence {current_sequence}")
            response = requests.post(
                f"{BACKEND_BASE_URL}{SUBMIT_TRANSACTION_ROUTE}",
                json=submit_data
            )
            
            if response.status_code != 200:
                error_msg = response.json().get('error', 'Unknown error')
                raise Exception(f"Failed to submit transfer: {error_msg}")
            
            result = response.json()
            def show_success():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[green]NFT transfer initiated successfully![/]\n{Pretty(result)}")
                except Exception as ui_error:
                    logger.error(f"Error showing success message: {str(ui_error)}")
            
            self.call_from_thread(show_success)
            
        except Exception as e:
            logger.error(f"Error transferring NFT: {str(e)}")
            def show_error():
                try:
                    result_display = self.query_one("#result-display", ResultDisplay)
                    if result_display:
                        result_display.update(f"[red]Error transferring NFT: {str(e)}[/]")
                except Exception as ui_error:
                    logger.error(f"Error showing error message: {str(ui_error)}")
            
            self.call_from_thread(show_error)

if __name__ == "__main__":
    app = NFTApp()
    app.run()
