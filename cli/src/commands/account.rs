use crate::client::{TtClient, TtError};
use crate::display;

pub async fn run(client: &TtClient) -> Result<(), TtError> {
    let data = client.get("/account").await?;
    display::print_account(&data);
    Ok(())
}
