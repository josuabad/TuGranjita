# Modelo de datos

## Lista de entidades y su función.

- ClienteProveedor: Representa a un cliente/proveedor en el sistema CRM
- Empleado: Representa a un empleado de la empresa
- Ganado: Representa al ganado de la granja
- ItemInventario: Representa cosas que compra la empresa que se necesiten por la granja (herramientas, alimentación...)
- LecturaSensor: Representa los datos recogidos de un sensor
- SensorIoT: Representa un sensor
- TransaccionCompraInventario: Representa la compra del inventario para la granja
- TransaccionCompraGanado: Representa la compra de ganado
- TransaccionVentaGanado: Representa la venta de ganado

## Relación entre entidades.

- ClienteProveedor se relaciona con: TransaccionCompraInventario, TransaccionCompraGanado y TransaccionVentaGanado, porque va a ser el modelo de entidad responsable de las compras/ventas de la empresa
- Ganado se relaciona con: SensorIoT (opcional) porque el ganado puede tener un sensor integrado de ubicación por motivos de seguridad, y TransaccionCompraGanado y TransaccionVentaGanado porque es la principal actividad económica de la empresa
- ItemInventario se relaciona con TransaccionCompraInventario
- LecturaSensor se relaciona con SensorIoT

## Decisiones tomadas (por qué esos campos y no otros).

Teniendo en cuenta que la empresa con la que estamos colaborando es un Granja que quiere modernizar sus sistemas en base a su actividad empresarial, nos encontramos con dos puntos críticos a tratar:

1. **Compra/Venta de ganado**
   Al tratar con la compra/venta de ganado nos debemos centrar en la calidad del servicio; es decir, no solo la trasancción si no también la gestión interna de los activos (ganado). Para eso, implementamos un red de sensores IoT con los que obtenemos datos relevantes al cuidado del animal, estamos hablando de sensores de humedad, de luminosidad, balanzas de peso... Con estos sensores podemos obtener información con la que optimizar y mejorar la calidad de nuestros activos.
   Con el fin de conseguir este objetivo y lograr la integración con distintas herramientas que nos permitan la monitorización, hemos diseñado los esquemas SensorIoT y LecturaSensor
2. **Sistemas de gestión**
   Podemos diferenciar la gestión en dos grupos
   1. Gestión interna: Contamos con los esquemas de Empleado, ItemInventario y TransaccionCompraInventario, cada una de las entidades con los atributos justos y necesarios para que podamos realizar las gestiones necesarias, buscando también cumplir con las regulaciones permitentes sobre el tratamiento de datos.
   2. Transacciones: Definimos las entidades de ClienteProveedor y Ganado siguiendo las mismas directrices comentadas anteriormente. También, las entidades de Transaccion con las que podemos llevar un historial bien definido de todas las transacciones de la empresa con las que podemos conectar a la empresa con herramientas (como un CRM) además de muchos beneficios como:
      - Cumplimiento legal y auditoría
      - Toma de decisiones estratégica
      - Optimización operativa
      - Análisis financiero y control de gastos

Todas estas decisiones han sido tomadas con el fin de digitalizar esta empresa y optimizar sus actividades para un mejor rendimiento económico. Un primera idea para probar la efectividad de los cambios es implementar un Dashboard en el que se integren estos sistemas, mediante el cual los administradores de la Granja puedan acceder y generar valor a la empresa.
