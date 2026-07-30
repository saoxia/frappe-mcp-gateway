from __future__ import annotations

from typing import Annotated

from mcp.server import MCPServer
from pydantic import Field

from frappe_mcp_gateway.frappe_client import FrappeClient


def register_personal_health_tools(server: MCPServer, client: FrappeClient):
	@server.tool()
	async def create_health_body_metrics(
		measurement_time: Annotated[str, Field(description="Measurement date or local date-time.")],
		weight: Annotated[float, Field(description="Body weight in kilograms.")],
		height: Annotated[float, Field(description="Height in centimeters.")],
		body_fat_percentage: float | None = None,
		fat_mass: float | None = None,
		basal_metabolic_rate: int | None = None,
		muscle_mass: float | None = None,
		muscle_percentage: float | None = None,
		protein_mass: float | None = None,
		protein_percentage: float | None = None,
		body_water_mass: float | None = None,
		body_water_percentage: float | None = None,
		bone_mineral_mass: float | None = None,
		bone_mineral_percentage: float | None = None,
		skeletal_muscle_mass: float | None = None,
		client_request_id: str | None = None,
		measurement_time_is_estimated: bool = False,
	) -> dict:
		"""Create body metrics after the user confirms the parsed values."""
		return await client.call(
			"personal.health.sidecar_api.create_health_body_metrics",
			{
				"measurement_time": measurement_time,
				"weight": weight,
				"height": height,
				"body_fat_percentage": body_fat_percentage,
				"fat_mass": fat_mass,
				"basal_metabolic_rate": basal_metabolic_rate,
				"muscle_mass": muscle_mass,
				"muscle_percentage": muscle_percentage,
				"protein_mass": protein_mass,
				"protein_percentage": protein_percentage,
				"body_water_mass": body_water_mass,
				"body_water_percentage": body_water_percentage,
				"bone_mineral_mass": bone_mineral_mass,
				"bone_mineral_percentage": bone_mineral_percentage,
				"skeletal_muscle_mass": skeletal_muscle_mass,
				"client_request_id": client_request_id,
				"measurement_time_is_estimated": measurement_time_is_estimated,
			},
		)

	@server.tool()
	async def get_health_body_metrics(
		name: str | None = None,
		start_date: str | None = None,
		end_date: str | None = None,
		limit: Annotated[int, Field(ge=1, le=100)] = 20,
	) -> dict:
		"""Get one body measurement or the current user's recent measurements."""
		return await client.call(
			"personal.health.sidecar_api.get_health_body_metrics",
			{
				"name": name,
				"start_date": start_date,
				"end_date": end_date,
				"limit": limit,
			},
		)
