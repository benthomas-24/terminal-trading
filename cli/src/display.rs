use colored::Colorize;
use serde_json::Value;

fn fmt_dollars(v: &Value) -> String {
    match v.as_f64() {
        Some(n) => format!("${:.2}", n),
        None => "—".to_string(),
    }
}

fn fmt_pct(v: &Value) -> String {
    match v.as_f64() {
        Some(n) => format!("{:.2}%", n * 100.0),
        None => "—".to_string(),
    }
}

fn pnl_color(v: &Value, s: String) -> String {
    match v.as_f64() {
        Some(n) if n > 0.0 => s.green().to_string(),
        Some(n) if n < 0.0 => s.red().to_string(),
        _ => s,
    }
}

pub fn print_account(data: &Value) {
    println!("{}", "── Account ─────────────────────────".bold());
    let rows = [
        ("Cash", fmt_dollars(&data["cash"])),
        ("Buying Power", fmt_dollars(&data["buying_power"])),
        ("Portfolio Value", fmt_dollars(&data["portfolio_value"])),
        ("Account #", data["account_number"].as_str().unwrap_or("—").to_string()),
    ];
    for (label, value) in &rows {
        println!("  {:<18} {}", label, value.bold());
    }
}

pub fn print_positions(data: &Value) {
    let positions = match data["positions"].as_array() {
        Some(p) if !p.is_empty() => p,
        _ => {
            println!("{}", "No open positions.".dimmed());
            return;
        }
    };
    println!("{}", "── Positions ───────────────────────────────────────────────".bold());
    println!(
        "  {:<8} {:>10} {:>14} {:>14} {:>12} {:>10}",
        "Symbol".underline(),
        "Qty".underline(),
        "Cost Basis".underline(),
        "Mkt Value".underline(),
        "P&L".underline(),
        "P&L %".underline(),
    );
    for pos in positions {
        let symbol = pos["symbol"].as_str().unwrap_or("?").to_uppercase();
        let qty = pos["quantity"].as_f64().map(|n| format!("{}", n)).unwrap_or_else(|| "—".to_string());
        let cost = fmt_dollars(&pos["cost_basis"]);
        let mkt = fmt_dollars(&pos["current_value"]);
        let pnl_str = fmt_dollars(&pos["unrealized_pnl"]);
        let pnl_pct_str = fmt_pct(&pos["unrealized_pnl_pct"]);
        let pnl_colored = pnl_color(&pos["unrealized_pnl"], pnl_str);
        let pct_colored = pnl_color(&pos["unrealized_pnl_pct"], pnl_pct_str);
        println!(
            "  {:<8} {:>10} {:>14} {:>14} {:>12} {:>10}",
            symbol.cyan().bold(),
            qty,
            cost,
            mkt,
            pnl_colored,
            pct_colored,
        );
    }
}

pub fn print_quote(data: &Value) {
    let symbol = data["symbol"].as_str().unwrap_or("?").to_uppercase();
    let last = fmt_dollars(&data["last_price"]);
    let change = fmt_dollars(&data["change"]);
    let change_pct = fmt_pct(&data["change_pct"]);
    let bid = fmt_dollars(&data["bid"]);
    let ask = fmt_dollars(&data["ask"]);
    let volume = data["volume"].as_u64().map(|v| format!("{}", v)).unwrap_or_else(|| "—".to_string());

    println!("{}", format!("── {} ─────────────────────────────", symbol).bold());
    println!("  {:<18} {}", "Last Price", last.bold().bright_white());
    let change_display = format!("{} ({})", change, change_pct);
    println!("  {:<18} {}", "Change", pnl_color(&data["change"], change_display));
    println!("  {:<18} {} / {}", "Bid / Ask", bid, ask);
    println!("  {:<18} {}", "Volume", volume);
}

pub fn print_portfolio(data: &Value) {
    println!("{}", "── Portfolio ───────────────────────".bold());
    println!("  {:<18} {}", "Total Value", fmt_dollars(&data["total_value"]).bold().bright_white());
    println!("  {:<18} {}", "Cash", fmt_dollars(&data["cash"]));
    println!("  {:<18} {}", "Equity Value", fmt_dollars(&data["equity_value"]));

    if let Some(positions) = data["positions"].as_array() {
        if !positions.is_empty() {
            println!();
            println!("  {}", "Holdings:".underline());
            for pos in positions {
                let symbol = pos["symbol"].as_str().unwrap_or("?").to_uppercase();
                let val = fmt_dollars(&pos["current_value"]);
                let pnl_str = fmt_dollars(&pos["unrealized_pnl"]);
                let pnl_colored = pnl_color(&pos["unrealized_pnl"], pnl_str);
                println!("    {:<10} {:>12}  P&L: {}", symbol.cyan(), val, pnl_colored);
            }
        }
    }
}
