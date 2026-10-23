// Native restore can give OMP a PATH without cmux. Use its supported CLI override.
export default function cmuxOmpCliPath() {
  if (!process.env.CMUX_OMP_CMUX_BIN && process.env.CMUX_BUNDLED_CLI_PATH) {
    process.env.CMUX_OMP_CMUX_BIN = process.env.CMUX_BUNDLED_CLI_PATH;
  }
}
