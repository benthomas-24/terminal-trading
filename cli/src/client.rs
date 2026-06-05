use serde_json::Value;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum TtError {
    #[error(
        "Python server is not running.\n  Start it with: cd server && uvicorn server:app --port 8765"
    )]
    ServerNotRunning,
    #[error("API error {0}: {1}")]
    ApiError(u16, String),
    #[error("Could not parse response: {0}")]
    ParseError(String),
}

pub struct TtClient {
    base_url: String,
    inner: reqwest::Client,
}

impl TtClient {
    pub fn new(base_url: &str) -> Self {
        Self {
            base_url: base_url.to_string(),
            inner: reqwest::Client::new(),
        }
    }

    pub async fn get(&self, path: &str) -> Result<Value, TtError> {
        let url = format!("{}{}", self.base_url, path);
        let resp = self.inner.get(&url).send().await.map_err(|e| {
            if e.is_connect() {
                TtError::ServerNotRunning
            } else {
                TtError::ApiError(0, e.to_string())
            }
        })?;

        let status = resp.status().as_u16();
        let body = resp.text().await.map_err(|e| TtError::ParseError(e.to_string()))?;

        if status >= 400 {
            return Err(TtError::ApiError(status, body));
        }

        serde_json::from_str(&body).map_err(|e| TtError::ParseError(e.to_string()))
    }
}
