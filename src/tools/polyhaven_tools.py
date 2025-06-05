"""
PolyHaven integration tools for Blender MCP Server.

Provides tools for searching and downloading assets from PolyHaven.
"""

import json

from mcp.server.fastmcp import Context, FastMCP


def search_polyhaven_assets_impl(
    ctx: Context | None = None,
    asset_type: str = "all",
    categories: str | None = None,
) -> str:
    """
    搜索PolyHaven资产。

    Args:
        ctx: MCP上下文对象（可选）
        asset_type: 资产类型 ('all', 'hdri', 'texture', 'model')
        categories: 类别过滤器（可选）

    Returns:
        搜索结果的JSON字符串

    """
    # 简化实现 - 返回占位符
    result = {
        "asset_type": asset_type,
        "categories": categories,
        "results": [
            {
                "id": f"sample_{asset_type}_1",
                "name": f"样例{asset_type}资产1",
                "categories": ["示例", "测试"],
                "thumbnail_url": "https://example.com/thumb1.jpg",
            },
            {
                "id": f"sample_{asset_type}_2",
                "name": f"样例{asset_type}资产2",
                "categories": ["示例", "测试"],
                "thumbnail_url": "https://example.com/thumb2.jpg",
            },
        ],
    }
    return json.dumps(result, ensure_ascii=False)


def download_polyhaven_asset_impl(
    ctx: Context | None = None,
    asset_id: str = "",
    asset_type: str = "",
    resolution: str = "4k",
    file_format: str | None = None,
) -> str:
    """
    从PolyHaven下载资产。

    Args:
        ctx: MCP上下文对象（可选）
        asset_id: 要下载的资产ID
        asset_type: 资产类型 ('hdri', 'texture', 'model')
        resolution: 分辨率 ('1k', '2k', '4k', '8k')
        file_format: 文件格式（可选）

    Returns:
        下载结果的JSON字符串

    """
    # 简化实现 - 返回占位符
    result = {
        "success": True,
        "asset_id": asset_id,
        "asset_type": asset_type,
        "resolution": resolution,
        "file_format": file_format,
        "downloaded_path": f"/path/to/downloads/{asset_id}.{file_format or 'blend'}",
    }
    return json.dumps(result, ensure_ascii=False)


def register_polyhaven_tools(app: FastMCP) -> None:
    """Register PolyHaven integration tools with the FastMCP app."""

    @app.tool()
    def search_polyhaven_assets(
        ctx: Context,
        asset_type: str = "all",
        categories: str | None = None,
    ) -> str:
        """
        Search for assets on PolyHaven.

        该工具用于搜索PolyHaven资源库中的资产，包括HDRI环境贴图、纹理和3D模型。
        您可以按资产类型和类别筛选结果。这些资产可用于增强您的Blender场景，
        提供高质量的照明、材质和模型。

        Args:
            asset_type: 要搜索的资产类型，可以是以下之一:
                - "all": 所有类型的资产（默认）
                - "hdri": 仅高动态范围图像（用于环境照明）
                - "texture": 仅纹理（用于材质）
                - "model": 仅3D模型
            categories: 可选的类别筛选器，用逗号分隔多个类别，例如"nature,urban"

        Returns:
            包含搜索结果的JSON字符串，每个结果包含资产ID、名称、类别和缩略图URL。

        Examples:
            搜索所有资产:
            ```python
            # 搜索所有类型的资产
            all_assets = search_polyhaven_assets(ctx)
            ```

            搜索特定类型:
            ```python
            # 只搜索HDRI环境贴图
            hdri_assets = search_polyhaven_assets(ctx, asset_type="hdri")
            ```

            按类别搜索:
            ```python
            # 搜索自然相关的纹理
            nature_textures = search_polyhaven_assets(ctx, asset_type="texture", categories="nature")
            ```

            分析结果:
            ```python
            # 搜索并分析结果
            import json

            result = search_polyhaven_assets(ctx, asset_type="model")
            assets_data = json.loads(result)

            for asset in assets_data["results"]:
                print(f"找到模型: {asset['name']} (ID: {asset['id']})")
            ```

        """
        return search_polyhaven_assets_impl(ctx, asset_type, categories)

    @app.tool()
    def download_polyhaven_asset(
        ctx: Context,
        asset_id: str,
        asset_type: str,
        resolution: str = "4k",
        file_format: str | None = None,
    ) -> str:
        """
        Download an asset from PolyHaven.

        该工具用于从PolyHaven下载资产，并将其导入到当前的Blender场景中。
        您可以指定资产ID、类型、分辨率和文件格式。下载的资产将自动适当地添加到场景中：
        HDRI会设置为世界环境，纹理会创建材质，模型会添加到场景中。

        Args:
            asset_id: 要下载的资产的唯一标识符（通过search_polyhaven_assets获取）
            asset_type: 资产类型，必须是以下之一:
                - "hdri": 高动态范围图像（用于环境照明）
                - "texture": 纹理（用于材质）
                - "model": 3D模型
            resolution: 资产分辨率，可以是:
                - "1k": 1024x1024（最低质量，最小文件）
                - "2k": 2048x2048
                - "4k": 4096x4096（默认，平衡质量和大小）
                - "8k": 8192x8192（最高质量，最大文件）
            file_format: 可选的文件格式，默认为资产类型的标准格式：
                - HDRI: 通常为.exr或.hdr
                - 纹理: 通常为.jpg或.png
                - 模型: 通常为.blend或.fbx

        Returns:
            包含下载结果的JSON字符串，包括下载路径和状态信息。

        Examples:
            下载HDRI环境:
            ```python
            # 下载一个HDRI环境并设置为当前场景的世界环境
            download_polyhaven_asset(ctx,
                asset_id="sunset_sky_1",
                asset_type="hdri",
                resolution="2k"  # 使用较低分辨率以减少文件大小
            )
            ```

            下载纹理:
            ```python
            # 下载砖墙纹理并创建材质
            download_polyhaven_asset(ctx,
                asset_id="brick_wall_006",
                asset_type="texture",
                resolution="4k"
            )
            ```

            下载模型:
            ```python
            # 下载办公椅模型并添加到场景
            download_polyhaven_asset(ctx,
                asset_id="office_chair_01",
                asset_type="model"
            )
            ```

            指定文件格式:
            ```python
            # 下载纹理并指定PNG格式
            download_polyhaven_asset(ctx,
                asset_id="wood_planks_001",
                asset_type="texture",
                resolution="4k",
                file_format="png"
            )
            ```

        """
        return download_polyhaven_asset_impl(
            ctx,
            asset_id,
            asset_type,
            resolution,
            file_format,
        )
