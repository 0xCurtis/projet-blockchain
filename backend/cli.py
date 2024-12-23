import click
import sys
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from rich.tree import Tree
import json
import os

console = Console()

# API Configuration
API_BASE_URL = "http://localhost:5000/api"

class AppState:
    def __init__(self):
        self.wallets = []
        self.tokens = []
        self.current_wallet = None
        self.load_state()

    def load_state(self):
        if os.path.exists('app_state.json'):
            try:
                with open('app_state.json', 'r') as f:
                    data = json.load(f)
                    self.wallets = data.get('wallets', [])
                    self.tokens = data.get('tokens', [])
                    if data.get('current_wallet'):
                        self.current_wallet = data['current_wallet']
            except:
                pass

    def save_state(self):
        with open('app_state.json', 'w') as f:
            json.dump({
                'wallets': self.wallets,
                'tokens': self.tokens,
                'current_wallet': self.current_wallet
            }, f, indent=2)

    def add_wallet(self, wallet_data):
        self.wallets.append(wallet_data)
        self.current_wallet = wallet_data
        self.save_state()

    def add_token(self, token_data):
        self.tokens.append(token_data)
        self.save_state()

app_state = AppState()

def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/tokens/wallet/info/test")
        return response.status_code != 500
    except:
        return False

def display_menu():
    console.clear()
    rprint(Panel.fit("🪙 Tokenized Asset Management CLI", style="bold green"))
    
    # Check API status
    api_status = "[green]Online[/green]" if check_api_health() else "[red]Offline[/red]"
    rprint(Panel.fit(f"API Status: {api_status}", style="blue"))
    
    # Display current wallet if selected
    if app_state.current_wallet:
        try:
            response = requests.get(f"{API_BASE_URL}/tokens/wallet/info/{app_state.current_wallet['address']}")
            if response.status_code == 200:
                data = response.json()['response']
                xrp_balance = float(data['account_info']['account_data']['Balance']) / 1_000_000
                
                rprint(Panel.fit(
                    f"""[blue]Current Wallet:[/blue] {app_state.current_wallet['address'][:8]}...{app_state.current_wallet['address'][-8:]}
[green]Balance:[/green] {xrp_balance} XRP
[blue]Explorer:[/blue] {data['explorer_url']}""",
                    style="blue"
                ))
        except:
            rprint("[red]Could not fetch wallet information[/red]")

    # Create menu table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="dim")
    table.add_column("Description")
    
    table.add_row("1", "Create New Wallet")
    table.add_row("2", "List Wallets")
    table.add_row("3", "Select Wallet")
    table.add_row("4", "Create Token")
    table.add_row("5", "List Tokens")
    table.add_row("6", "View Current State")
    table.add_row("7", "View Wallet Details")
    table.add_row("q", "Quit")
    
    console.print(table)

def create_new_wallet():
    try:
        response = requests.post(f"{API_BASE_URL}/tokens/wallet/create")
        if response.status_code == 200:
            data = response.json()['response']
            wallet_data = {
                'address': data['address'],
                'seed': data['seed']
            }
            app_state.add_wallet(wallet_data)
            
            rprint(Panel.fit(f"""[green]Wallet Created Successfully![/green]
Address: {data['address']}
Secret: {data['seed']}
Explorer: {data['explorer_url']}"""))
        else:
            rprint(f"[red]Error: {response.json().get('error', 'Unknown error')}[/red]")
    except Exception as e:
        rprint(f"[red]Error creating wallet: {str(e)}[/red]")

def list_wallets():
    if not app_state.wallets:
        rprint("[yellow]No wallets found![/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Index")
    table.add_column("Address")
    table.add_column("XRP Balance")
    table.add_column("Status")

    for idx, wallet in enumerate(app_state.wallets):
        try:
            response = requests.get(f"{API_BASE_URL}/tokens/wallet/info/{wallet['address']}")
            if response.status_code == 200:
                data = response.json()['response']
                xrp_balance = float(data['account_info']['account_data']['Balance']) / 1_000_000
                status = "Active" if app_state.current_wallet and app_state.current_wallet['address'] == wallet['address'] else ""
                table.add_row(str(idx), wallet['address'], f"{xrp_balance} XRP", status)
        except:
            table.add_row(str(idx), wallet['address'], "Error", "Error")
    
    console.print(table)

def view_wallet_details():
    if not app_state.current_wallet:
        rprint("[red]Please select a wallet first![/red]")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/tokens/wallet/info/{app_state.current_wallet['address']}")
        if response.status_code == 200:
            data = response.json()['response']
            
            tree = Tree(f"[bold blue]Wallet Details")
            
            # Basic Info
            basic_info = tree.add("📊 Basic Information")
            xrp_balance = float(data['account_info']['account_data']['Balance']) / 1_000_000
            basic_info.add(f"XRP Balance: {xrp_balance} XRP")
            basic_info.add(f"Address: {app_state.current_wallet['address']}")
            basic_info.add(f"Explorer: {data['explorer_url']}")

            # Trust Lines and Tokens
            if 'lines' in data['account_lines']:
                tokens = tree.add("🪙 Issued Tokens")
                for line in data['account_lines']['lines']:
                    tokens.add(f"Currency: {line['currency']}, Balance: {line['balance']}")

            console.print(tree)
        else:
            rprint(f"[red]Error: {response.json().get('error', 'Unknown error')}[/red]")
    except Exception as e:
        rprint(f"[red]Error fetching wallet details: {str(e)}[/red]")

def select_wallet():
    list_wallets()
    if not app_state.wallets:
        return

    try:
        idx = click.prompt("Enter wallet index to select", type=int)
        if 0 <= idx < len(app_state.wallets):
            app_state.current_wallet = app_state.wallets[idx]
            app_state.save_state()
            rprint(f"[green]Selected wallet: {app_state.current_wallet['address']}[/green]")
        else:
            rprint("[red]Invalid wallet index![/red]")
    except ValueError:
        rprint("[red]Please enter a valid number![/red]")

def get_token_metadata():
    """Interactive questionnaire to collect token metadata"""
    metadata = {}
    
    # Basic Information
    rprint("\n[bold blue]Token Details[/bold blue]")
    metadata["description"] = click.prompt("Description", type=str)
    
    # Optional Information
    if click.confirm("Would you like to add a website?", default=True):
        metadata["website"] = click.prompt("Website URL", type=str)
    
    if click.confirm("Would you like to add social media links?", default=True):
        metadata["social"] = {}
        while True:
            platform = click.prompt("Social media platform (e.g., twitter, discord)", type=str).lower()
            link = click.prompt(f"{platform.capitalize()} link", type=str)
            metadata["social"][platform] = link
            if not click.confirm("Add another social media link?", default=False):
                break
    
    # Additional Properties
    if click.confirm("Would you like to add any additional properties?", default=False):
        metadata["properties"] = {}
        while True:
            key = click.prompt("Property name", type=str)
            value = click.prompt("Property value", type=str)
            metadata["properties"][key] = value
            if not click.confirm("Add another property?", default=False):
                break
    
    return metadata

def create_token():
    if not app_state.current_wallet:
        rprint("[red]Please select a wallet first![/red]")
        return

    try:
        # Token Basic Information
        rprint("\n[bold green]Create New Token[/bold green]")
        name = click.prompt("Token Name")
        supply = click.prompt("Total Supply", type=int)
        
        # Get metadata through interactive questionnaire
        rprint("\n[bold yellow]Let's collect some metadata for your token[/bold yellow]")
        token_metadata = get_token_metadata()

        # Preview the metadata
        rprint("\n[bold blue]Token Metadata Preview:[/bold blue]")
        rprint(Panel.fit(json.dumps(token_metadata, indent=2), title="Metadata"))
        
        if not click.confirm("\nDo you want to proceed with this metadata?", default=True):
            rprint("[yellow]Token creation cancelled[/yellow]")
            return

        # Create wallet dictionary with the correct structure
        wallet_data = {
            "classic_address": app_state.current_wallet['address'],
            "secret": app_state.current_wallet['seed']
        }

        data = {
            "wallet": wallet_data,  # Use the properly structured wallet data
            "name": name,
            "supply": supply,
            "metadata": token_metadata
        }
        
        with console.status("[bold green]Creating token on XRPL...[/bold green]"):
            response = requests.post(f"{API_BASE_URL}/tokens/create", json=data)
        
        if response.status_code == 200:
            response_data = response.json()['response']
            if response_data["success"]:
                token_data = {
                    'name': name,
                    'supply': supply,
                    'token_metadata': token_metadata,
                    'wallet': app_state.current_wallet['address'],
                    'tx_response': response_data
                }
                app_state.add_token(token_data)
                
                # Display success message with explorer links
                rprint("\n[bold green]🎉 Token Created Successfully! 🎉[/bold green]")
                
                # Basic token information
                rprint(Panel.fit(f"""[bold blue]Token Details[/bold blue]
Name: {name}
Currency Code: {response_data['currency_code']}
Total Supply: {supply}
Issuer: {response_data['issuer'][:8]}...{response_data['issuer'][-8:]}"""))
                
                # Metadata display
                if token_metadata:
                    metadata_panel = Panel.fit(
                        json.dumps(token_metadata, indent=2),
                        title="[bold blue]Token Metadata[/bold blue]"
                    )
                    rprint(metadata_panel)
                
                # Explorer Links with verification instructions
                explorer_panel = Panel.fit(f"""[bold blue]🔍 Verify Your Token on XRPL Explorer[/bold blue]

1. View Token Issuance Transaction:
   [link={response_data['explorer_urls']['payment_tx']}]{response_data['explorer_urls']['payment_tx']}[/link]

2. View Issuer Account:
   [link={response_data['explorer_urls']['account']}]{response_data['explorer_urls']['account']}[/link]

3. Transaction Steps:
   • Enable Rippling: [link={response_data['explorer_urls']['enable_tx']}]View Transaction[/link]
   • Create Trustline: [link={response_data['explorer_urls']['trust_tx']}]View Transaction[/link]
   • Issue Token: [link={response_data['explorer_urls']['payment_tx']}]View Transaction[/link]

[yellow]👉 Click the links above to verify your token on the XRPL Explorer[/yellow]""",
                    title="[bold green]Verification Links[/bold green]")
                
                rprint(explorer_panel)
                
            else:
                rprint(f"[red]Error: {response_data['error']}[/red]")
        else:
            rprint(f"[red]Error: {response.json().get('error', 'Unknown error')}[/red]")
            
    except Exception as e:
        rprint(f"[red]Error creating token: {str(e)}[/red]")

def list_tokens():
    if not app_state.tokens:
        rprint("[yellow]No tokens found![/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Name")
    table.add_column("Supply")
    table.add_column("Wallet")
    table.add_column("Currency Code")
    table.add_column("Metadata")
    table.add_column("Explorer")

    for token in app_state.tokens:
        explorer_url = token['tx_response']['explorer_urls']['payment_tx']
        metadata_str = json.dumps(token.get('token_metadata', {}), sort_keys=True)[:50] + "..."
        table.add_row(
            token['name'],
            str(token['supply']),
            f"{token['wallet'][:8]}...{token['wallet'][-8:]}",
            token['tx_response']['currency_code'],
            metadata_str,
            explorer_url
        )
    
    console.print(table)

def view_state():
    if not app_state.current_wallet:
        rprint("[yellow]No wallet selected[/yellow]")
        return

    try:
        response = requests.get(f"{API_BASE_URL}/tokens/wallet/info/{app_state.current_wallet['address']}")
        if response.status_code == 200:
            data = response.json()['response']
            xrp_balance = float(data['account_info']['account_data']['Balance']) / 1_000_000

            state_data = {
                'wallets_count': len(app_state.wallets),
                'tokens_count': len(app_state.tokens),
                'current_wallet': {
                    'address': app_state.current_wallet['address'],
                    'xrp_balance': f"{xrp_balance} XRP",
                    'explorer_url': data['explorer_url']
                }
            }
            
            rprint(Panel.fit(json.dumps(state_data, indent=2), title="Current State"))
        else:
            rprint(f"[red]Error: {response.json().get('error', 'Unknown error')}[/red]")
    except Exception as e:
        rprint(f"[red]Error fetching state: {str(e)}[/red]")

def main_menu():
    while True:
        display_menu()
        choice = click.prompt("Enter your choice", type=str).lower()
        
        if choice == 'q':
            sys.exit(0)
        elif choice == '1':
            create_new_wallet()
        elif choice == '2':
            list_wallets()
        elif choice == '3':
            select_wallet()
        elif choice == '4':
            create_token()
        elif choice == '5':
            list_tokens()
        elif choice == '6':
            view_state()
        elif choice == '7':
            view_wallet_details()
        else:
            rprint("[red]Invalid choice![/red]")
        
        click.pause()

if __name__ == "__main__":
    if not check_api_health():
        rprint("[red]Error: API is not running. Please start the Flask server first.[/red]")
        sys.exit(1)
    main_menu() 