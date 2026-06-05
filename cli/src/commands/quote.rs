use crate::client::{TtClient, TtError};
use crate::display;

pub async fn run(client: &TtClient, symbol: &str) -> Result<(), TtError> {
    let data = client.get(&format!("/quote/{}", symbol.to_uppercase())).await?;
    display::print_quote(&data);
    Ok(())
}
