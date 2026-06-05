use crate::client::{TtClient, TtError};
use crate::display;

pub async fn run(client: &TtClient) -> Result<(), TtError> {
    let data = client.get("/positions").await?;
    display::print_positions(&data);
    Ok(())
}
