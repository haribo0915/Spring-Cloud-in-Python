# -*- coding: utf-8 -*-
# standard library
from http.server import HTTPServer
from typing import Callable, List, Optional

# scip plugin
from spring_cloud.commons.http import RestTemplate
from spring_cloud.gateway.filter.global_filter import RestTemplateRouteFilter
from spring_cloud.gateway.handler import DispatcherHandler
from spring_cloud.gateway.handler.handler import FilteringWebHandler, RoutePredicateHandlerMapping
from spring_cloud.gateway.route.builder.route_locator import RouteLocator, RouteLocatorBuilder
from spring_cloud.gateway.server.request_handler import HTTPRequestHandler
from spring_cloud.utils import logging, validate

__author__ = "Waterball (johnny850807@gmail.com)"
__license__ = "Apache 2.0"


class ApiGatewayApplication:
    @staticmethod
    def run(
        route_locator_builder_consumer: Callable[[RouteLocatorBuilder], RouteLocator],
        host_name: Optional[str] = "0.0.0.0",
        port_: Optional[int] = 8726,
        enable_discovery_client: Optional[bool] = False,
        eureka_server_urls: Optional[List[str]] = None,
    ):
        __logger = logging.getLogger("spring_cloud.ApiGatewayApplication")
        api = None
        web_server = None
        try:

            __logger.info(f"Launching ApiGatewayApplication listening at {host_name}:{port_}")
            if enable_discovery_client:
                validate.not_none(eureka_server_urls)
                __logger.debug("The discovery client routing is enabled.")
                # scip plugin
                import spring_cloud.context.bootstrap_client as spring_cloud_bootstrap

                api = spring_cloud_bootstrap.enable_service_discovery(
                    service_id="ApiGateway", port=port_, eureka_server_urls=eureka_server_urls
                )
            else:
                api = RestTemplate()

            route_locator = route_locator_builder_consumer(RouteLocatorBuilder())
            __logger.debug(str(route_locator))

            route_mapping = RoutePredicateHandlerMapping(route_locator)
            filtering_web_handler = FilteringWebHandler([RestTemplateRouteFilter(api)])
            dispatcher_handler = DispatcherHandler(route_mapping, filtering_web_handler)

            web_server = HTTPServer(
                (host_name, port_),
                lambda *args, **kwargs: HTTPRequestHandler(*args, dispatcher_handler=dispatcher_handler, **kwargs),
            )

            __logger.info(f"Server listening at {host_name}:{port_}")

            web_server.serve_forever()
        except KeyboardInterrupt:
            pass
        except Exception as err:
            __logger.error(str(err))

        if web_server:
            web_server.server_close()
            __logger.info("Server stopped.")
        if api:
            api.shutdown()
