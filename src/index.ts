import { Container, getContainer } from "@cloudflare/containers";

export class StreamlitContainer extends Container {
  defaultPort = 8501;
  sleepAfter = "30m";
  pingEndpoint = "/_stcore/health";
  enableInternet = true;
}

interface Env {
  STREAMLIT: DurableObjectNamespace<StreamlitContainer>;
  CLICKHOUSE_HOST?: string;
  CLICKHOUSE_PORT?: string;
  CLICKHOUSE_USER?: string;
  CLICKHOUSE_PASSWORD?: string;
  CLICKHOUSE_DATABASE?: string;
  CLICKHOUSE_SECURE?: string;
}

function clickhouseEnv(env: Env): Record<string, string> {
  return Object.fromEntries(
    [
      "CLICKHOUSE_HOST",
      "CLICKHOUSE_PORT",
      "CLICKHOUSE_USER",
      "CLICKHOUSE_PASSWORD",
      "CLICKHOUSE_DATABASE",
      "CLICKHOUSE_SECURE",
    ]
      .map((key) => [key, env[key as keyof Env]])
      .filter((entry): entry is [string, string] => typeof entry[1] === "string"),
  );
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const container = getContainer(env.STREAMLIT, "megasena-streamlit");
    await container.startAndWaitForPorts({
      ports: 8501,
      startOptions: {
        envVars: clickhouseEnv(env),
      },
    });

    return container.fetch(request);
  },
};
