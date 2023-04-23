use regex::bytes::{Regex, RegexBuilder};

pub struct Pattern {
    pub regex: Regex,
}

impl Pattern {
    pub fn new(pattern: &str) -> Self {
        let patt: String = pattern
            .replace('?', "*")
            .split(' ')
            .map(|b| match b {
                "*" | "**" => ".".to_string(),
                _ => format!("\\x{}", b),
            })
            .collect();
        let regex = RegexBuilder::new(patt.as_str())
            .dot_matches_new_line(false)
            .case_insensitive(false)
            .unicode(false)
            .build()
            .unwrap();
        Self { regex }
    }

    pub fn scan(&self, data: &[u8]) -> Option<usize> {
        self.regex.find(data).map(|m| m.start())
    }
}
