#[cfg(windows)]
use embed_resource;

fn main() {
    embed_resource::compile("dofus-helpers.rc", embed_resource::NONE);
}
