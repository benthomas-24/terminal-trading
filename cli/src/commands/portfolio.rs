use crate::client::{TtClient, TtError};
use crate::display;

pub async fn run(client: &TtClient) -> Result<(), TtError> {
    let data = client.get("/portfolio").await?;
    display::print_portfolio(&data);
    Ok(())
}
