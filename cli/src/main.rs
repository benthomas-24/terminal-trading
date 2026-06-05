mod client;
mod commands;
mod display;

use clap::{Parser, Subcommand};
use colored::Colorize;

const SERVER_URL: &str = "http://127.0.0.1:8765";

#[derive(Parser)]
#[command(name = "tt", about = "Terminal Trading — Public.com CLI", version)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Show account balance and buying power
    Account,
    /// Show open positions with P&L
    Positions,
    /// Get a real-time quote for a symbol
    Quote {
        /// Ticker symbol (e.g. AAPL, BTC)
        symbol: String,
    },
    /// Show full portfolio overview
    Portfolio,
}

#[tokio::main]
async fn main() {
    let cli = Cli::parse();
    let client = client::TtClient::new(SERVER_URL);

    let result = match cli.command {
        Commands::Account => commands::account::run(&client).await,
        Commands::Positions => commands::positions::run(&client).await,
        Commands::Quote { symbol } => commands::quote::run(&client, &symbol).await,
        Commands::Portfolio => commands::portfolio::run(&client).await,
    };

    if let Err(e) = result {
        eprintln!("{} {}", "error:".red().bold(), e);
        std::process::exit(1);
    }
}
