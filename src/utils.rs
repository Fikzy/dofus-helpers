use hex;

pub fn parse_bytearray(bytearray: &str) -> Vec<u8> {
    bytearray
        .split(' ')
        .flat_map(|b| hex::decode(b).unwrap())
        .collect()
}
