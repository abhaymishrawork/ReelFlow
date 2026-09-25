# Matte model

Styles that put text behind the speaker need `u2net_human_seg.onnx` (~168 MB, Apache-2.0). The engine looks
for it in this order:

1. The `CAPTIONFX_MATTE_MODEL` environment variable
2. `engine/models/u2net_human_seg.onnx` (this folder, git-ignored)
3. `~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx` (cached by `hyperframes remove-background`)
4. `~/.u2net/u2net_human_seg.onnx` (cached by `rembg`)

The matte is computed once per video and cached as `<workdir>/matte.mkv`. Use `--rematte` to rebuild it and
`--matte-every 2` to halve the matting time on long videos.
